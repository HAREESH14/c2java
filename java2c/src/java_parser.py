# ─────────────────────────────────────────────────────────────────────────────
#  java_parser.py
#  Recursive Descent Parser for Java source code.
#  Parses basic Java → builds a Java AST.
# ─────────────────────────────────────────────────────────────────────────────

from java_lexer import TT, Token
from java_ast_nodes import *

PRIMITIVE_TYPES = {'int', 'float', 'double', 'char', 'void', 'boolean'}
ALL_TYPES       = PRIMITIVE_TYPES | {'String', 'HashMap'}


class JavaParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    def current(self):
        return self.tokens[self.pos]

    def peek(self, offset=1):
        i = self.pos + offset
        return self.tokens[i] if i < len(self.tokens) else self.tokens[-1]

    def advance(self):
        tok = self.tokens[self.pos]
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def expect(self, type_):
        tok = self.current()
        if tok.type != type_:
            raise SyntaxError(
                f'[JavaParser] Line {tok.line}: Expected {type_!r} got {tok.type!r} ({tok.value!r})'
            )
        return self.advance()

    def match(self, *types):
        return self.current().type in types

    def match_val(self, *values):
        return self.current().value in values

    # ── Program: skip import, parse class ────────────────────────────────────
    def parse(self):
        # Skip import statements
        while self.match('import'):
            while not self.match(TT.SEMI):
                self.advance()
            self.advance()

        # public class ClassName {
        if self.match('public'):  self.advance()
        self.expect('class')
        class_name = self.expect(TT.ID).value
        self.expect(TT.LBRACE)

        methods = []
        while not self.match(TT.RBRACE) and not self.match(TT.EOF):
            methods.append(self.parse_method())

        self.expect(TT.RBRACE)
        return JProgramNode(class_name, methods)

    # ── Method declaration ────────────────────────────────────────────────────
    def parse_method(self):
        # Consume modifiers: public, private, static
        while self.match_val('public', 'private', 'static'):
            self.advance()

        ret_type = self.parse_type()
        name     = self.expect(TT.ID).value
        is_main  = (name == 'main')

        self.expect(TT.LPAREN)
        params = []
        if not self.match(TT.RPAREN):
            params = self.parse_param_list()
        self.expect(TT.RPAREN)

        body = self.parse_block()
        return JMethodNode(ret_type, name, params, body, is_main)

    def parse_type(self):
        """Parse a type: int, float, void, int[], HashMap<K,V>, String[], etc."""
        tok = self.current()

        # HashMap<K,V>
        if tok.value == 'HashMap':
            self.advance()
            self.expect(TT.LT)
            k = self.parse_generic_type()
            self.expect(TT.COMMA)
            v = self.parse_generic_type()
            self.expect(TT.GT)
            return f'HashMap<{k},{v}>'

        if tok.type not in (TT.ID,) and tok.value not in ALL_TYPES:
            raise SyntaxError(f'[JavaParser] Line {tok.line}: Expected type, got {tok.value!r}')

        self.advance()
        type_str = tok.value

        # Array suffix: int[]  int[][]
        while self.match(TT.LBRACK) and self.peek().type == TT.RBRACK:
            self.advance(); self.advance()
            type_str += '[]'

        return type_str

    def parse_generic_type(self):
        tok = self.current()
        self.advance()
        return tok.value

    def parse_param_list(self):
        params = [self.parse_param()]
        while self.match(TT.COMMA):
            self.advance()
            # Skip String[] args
            params.append(self.parse_param())
        return params

    def parse_param(self):
        type_ = self.parse_type()
        # String[] args — skip
        if type_ == 'String[]':
            name = self.expect(TT.ID).value
            return JParamNode('void', name, False)  # skip in C output

        name     = self.expect(TT.ID).value
        is_array = '[]' in type_
        base     = type_.replace('[]', '')
        return JParamNode(base, name, is_array)

    # ── Block ─────────────────────────────────────────────────────────────────
    def parse_block(self):
        self.expect(TT.LBRACE)
        stmts = []
        while not self.match(TT.RBRACE) and not self.match(TT.EOF):
            stmt = self.parse_statement()
            if stmt is not None:
                stmts.append(stmt)
        self.expect(TT.RBRACE)
        return JBlockNode(stmts)

    # ── Statement dispatcher ──────────────────────────────────────────────────
    def parse_statement(self):
        cur = self.current()

        # Variable / array declaration starts with a type
        if cur.value in PRIMITIVE_TYPES or (cur.type == TT.ID and self.is_type_ahead()):
            return self.parse_declaration()

        # HashMap declaration
        if cur.value == 'HashMap':
            return self.parse_hashmap_decl()

        if cur.value == 'if':    return self.parse_if()
        if cur.value == 'for':   return self.parse_for()
        if cur.value == 'while': return self.parse_while()
        if cur.value == 'do':    return self.parse_do_while()
        if cur.value == 'return':return self.parse_return()

        # System.out.println / System.out.printf
        if cur.value == 'System':
            return self.parse_sysout()

        # ID-starting: assignment, array assign, method call, map.put, map operations
        if cur.type == TT.ID:
            return self.parse_id_statement()

        # Skip unknown tokens gracefully
        self.advance()
        return None

    def is_type_ahead(self):
        """Lookahead: is current token a type followed by an identifier?"""
        cur  = self.current()
        nxt  = self.peek(1)
        nxt2 = self.peek(2)
        if cur.value in ALL_TYPES and nxt.type == TT.ID:
            return True
        if cur.value in ALL_TYPES and nxt.type == TT.LBRACK and nxt2.type == TT.RBRACK:
            return True
        return False

    # ── Variable / Array declaration ──────────────────────────────────────────
    def parse_declaration(self):
        type_ = self.parse_type()
        name  = self.expect(TT.ID).value

        is_array = '[]' in type_
        base     = type_.replace('[]', '')

        if is_array:
            return self.parse_array_decl_rest(base, name)

        # Check for 2D array name[][] = new T[r][c]
        if self.match(TT.LBRACK):
            # Could be: name[5]; or name[][] =
            return self.parse_array_decl_rest(base, name)

        # Simple variable
        init = None
        if self.match(TT.ASSIGN):
            self.advance()
            init = self.parse_expression()
        self.expect(TT.SEMI)
        return JVarDeclNode(base, name, init)

    def parse_array_decl_rest(self, base_type, name):
        """Handle array declaration after type and name are parsed."""
        # int[][] matrix = new int[3][3];  →  already consumed type as 'int[][]'
        # OR int[] arr = new int[5];
        # OR int[] arr = {1,2,3};

        self.expect(TT.ASSIGN)

        # new int[5]  or  new int[3][3]
        if self.match_val('new'):
            self.advance()           # consume 'new'
            self.parse_type()        # consume element type (e.g. 'int')
            self.expect(TT.LBRACK)
            size1 = self.parse_expression()
            self.expect(TT.RBRACK)

            # 2D: new int[3][3]
            if self.match(TT.LBRACK):
                self.advance()
                size2 = self.parse_expression()
                self.expect(TT.RBRACK)
                self.expect(TT.SEMI)
                return JArray2DDeclNode(base_type, name, size1, size2)

            self.expect(TT.SEMI)
            return JArrayDeclNode(base_type, name, size=size1)

        # Initializer list: {1, 2, 3}
        if self.match(TT.LBRACE):
            self.advance()
            values = []
            if not self.match(TT.RBRACE):
                values.append(self.parse_expression())
                while self.match(TT.COMMA):
                    self.advance()
                    values.append(self.parse_expression())
            self.expect(TT.RBRACE)
            self.expect(TT.SEMI)
            return JArrayDeclNode(base_type, name, init_values=values)

        # Fallback
        self.expect(TT.SEMI)
        return JArrayDeclNode(base_type, name)

    # ── HashMap declaration ───────────────────────────────────────────────────
    def parse_hashmap_decl(self):
        self.advance()   # 'HashMap'
        self.expect(TT.LT)
        kt = self.advance().value  # key type
        self.expect(TT.COMMA)
        vt = self.advance().value  # val type
        self.expect(TT.GT)
        name = self.expect(TT.ID).value
        self.expect(TT.ASSIGN)
        # consume: new HashMap<>()
        self.advance()   # new
        self.advance()   # HashMap
        if self.match(TT.LT): self.advance()
        if self.match(TT.GT): self.advance()
        self.expect(TT.LPAREN)
        self.expect(TT.RPAREN)
        self.expect(TT.SEMI)
        return JHashMapDeclNode(kt, vt, name)

    # ── System.out.println / printf ───────────────────────────────────────────
    def parse_sysout(self):
        self.advance()              # System
        self.expect(TT.DOT)
        self.expect(TT.ID)          # out
        self.expect(TT.DOT)
        method = self.expect(TT.ID).value   # println / print / printf
        self.expect(TT.LPAREN)

        if method == 'printf':
            fmt = self.expect(TT.STRING).value
            args = []
            while self.match(TT.COMMA):
                self.advance()
                args.append(self.parse_expression())
            self.expect(TT.RPAREN)
            self.expect(TT.SEMI)
            return JPrintlnNode(args, is_printf=True, format_str=fmt)
        else:
            # println / print
            args = []
            if not self.match(TT.RPAREN):
                args.append(self.parse_expression())
            self.expect(TT.RPAREN)
            self.expect(TT.SEMI)
            return JPrintlnNode(args, is_printf=False)

    # ── ID-starting statements ────────────────────────────────────────────────
    def parse_id_statement(self):
        name = self.advance().value

        # map.put(k, v) or map.get(k) or map.containsKey(k)
        if self.match(TT.DOT):
            self.advance()
            method = self.expect(TT.ID).value
            self.expect(TT.LPAREN)
            if method == 'put':
                key = self.parse_expression()
                self.expect(TT.COMMA)
                val = self.parse_expression()
                self.expect(TT.RPAREN)
                self.expect(TT.SEMI)
                return JMapPutNode(name, key, val)
            # other method calls — parse args generically
            args = []
            if not self.match(TT.RPAREN):
                args.append(self.parse_expression())
                while self.match(TT.COMMA):
                    self.advance()
                    args.append(self.parse_expression())
            self.expect(TT.RPAREN)
            self.expect(TT.SEMI)
            return JMethodCallStmtNode(f'{name}.{method}', args)

        # 2D array assign: m[i][j] = expr
        if self.match(TT.LBRACK) and self.peek(2).type == TT.RBRACK \
                and self.peek(3).type == TT.LBRACK:
            self.advance()
            row = self.parse_expression()
            self.expect(TT.RBRACK)
            self.advance()
            col = self.parse_expression()
            self.expect(TT.RBRACK)
            self.expect(TT.ASSIGN)
            val = self.parse_expression()
            self.expect(TT.SEMI)
            return JArray2DAssignNode(name, row, col, val)

        # 1D array assign: arr[i] = expr
        if self.match(TT.LBRACK):
            self.advance()
            index = self.parse_expression()
            self.expect(TT.RBRACK)
            self.expect(TT.ASSIGN)
            val = self.parse_expression()
            self.expect(TT.SEMI)
            return JArrayAssignNode(name, index, val)

        # Method call: func(args)
        if self.match(TT.LPAREN):
            self.advance()
            args = []
            if not self.match(TT.RPAREN):
                args.append(self.parse_expression())
                while self.match(TT.COMMA):
                    self.advance()
                    args.append(self.parse_expression())
            self.expect(TT.RPAREN)
            self.expect(TT.SEMI)
            return JMethodCallStmtNode(name, args)

        # Simple assign: x = expr
        self.expect(TT.ASSIGN)
        val = self.parse_expression()
        self.expect(TT.SEMI)
        return JAssignNode(name, val)

    # ── if / else if / else ───────────────────────────────────────────────────
    def parse_if(self):
        self.advance()   # 'if'
        self.expect(TT.LPAREN)
        cond = self.parse_expression()
        self.expect(TT.RPAREN)
        body = self.parse_block()
        branches = [(cond, body)]

        else_block = None
        while self.match_val('else'):
            self.advance()
            if self.match_val('if'):
                self.advance()
                self.expect(TT.LPAREN)
                cond2 = self.parse_expression()
                self.expect(TT.RPAREN)
                body2 = self.parse_block()
                branches.append((cond2, body2))
            else:
                else_block = self.parse_block()
                break

        return JIfNode(branches, else_block)

    # ── for loop ──────────────────────────────────────────────────────────────
    def parse_for(self):
        self.advance()   # 'for'
        self.expect(TT.LPAREN)

        # init
        if self.current().value in PRIMITIVE_TYPES:
            type_ = self.parse_type()
            name  = self.expect(TT.ID).value
            self.expect(TT.ASSIGN)
            val   = self.parse_expression()
            init  = JVarDeclNode(type_, name, val)
        else:
            n = self.expect(TT.ID).value
            self.expect(TT.ASSIGN)
            val  = self.parse_expression()
            init = JAssignNode(n, val)

        self.expect(TT.SEMI)
        cond = self.parse_expression()
        self.expect(TT.SEMI)
        update = self.parse_for_update()
        self.expect(TT.RPAREN)
        body = self.parse_block()
        return JForNode(init, cond, update, body)

    def parse_for_update(self):
        name = self.expect(TT.ID).value
        op   = self.current().type
        if op == TT.INC:   self.advance(); return JUpdateNode(name, '++')
        if op == TT.DEC:   self.advance(); return JUpdateNode(name, '--')
        if op == TT.PLUSEQ:  self.advance(); return JUpdateNode(name, '+=', self.parse_expression())
        if op == TT.MINUSEQ: self.advance(); return JUpdateNode(name, '-=', self.parse_expression())
        self.expect(TT.ASSIGN)
        return JUpdateNode(name, '=', self.parse_expression())

    # ── while ─────────────────────────────────────────────────────────────────
    def parse_while(self):
        self.advance()
        self.expect(TT.LPAREN)
        cond = self.parse_expression()
        self.expect(TT.RPAREN)
        body = self.parse_block()
        return JWhileNode(cond, body)

    # ── do-while ──────────────────────────────────────────────────────────────
    def parse_do_while(self):
        self.advance()
        body = self.parse_block()
        self.advance()   # while
        self.expect(TT.LPAREN)
        cond = self.parse_expression()
        self.expect(TT.RPAREN)
        self.expect(TT.SEMI)
        return JDoWhileNode(body, cond)

    # ── return ────────────────────────────────────────────────────────────────
    def parse_return(self):
        self.advance()
        val = None
        if not self.match(TT.SEMI):
            val = self.parse_expression()
        self.expect(TT.SEMI)
        return JReturnNode(val)

    # ── Expressions ───────────────────────────────────────────────────────────
    def parse_expression(self):  return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.match(TT.OR):
            op = self.advance().value; right = self.parse_and()
            left = JBinOpNode(left, op, right)
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.match(TT.AND):
            op = self.advance().value; right = self.parse_equality()
            left = JBinOpNode(left, op, right)
        return left

    def parse_equality(self):
        left = self.parse_relational()
        while self.match(TT.EQ, TT.NEQ):
            op = self.advance().value; right = self.parse_relational()
            left = JBinOpNode(left, op, right)
        return left

    def parse_relational(self):
        left = self.parse_additive()
        while self.match(TT.LT, TT.GT, TT.LTE, TT.GTE):
            op = self.advance().value; right = self.parse_additive()
            left = JBinOpNode(left, op, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.match(TT.PLUS, TT.MINUS):
            op = self.advance().value; right = self.parse_multiplicative()
            left = JBinOpNode(left, op, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.match(TT.STAR, TT.SLASH, TT.MOD):
            op = self.advance().value; right = self.parse_unary()
            left = JBinOpNode(left, op, right)
        return left

    def parse_unary(self):
        if self.match(TT.NOT):
            op = self.advance().value
            return JUnaryOpNode(op, self.parse_unary())
        if self.match(TT.MINUS):
            op = self.advance().value
            return JUnaryOpNode(op, self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        tok = self.current()

        if tok.type == TT.INT_LIT:   self.advance(); return JIntLiteralNode(tok.value)
        if tok.type == TT.FLOAT_LIT: self.advance(); return JFloatLiteralNode(tok.value)
        if tok.type == TT.CHAR_LIT:  self.advance(); return JCharLiteralNode(tok.value)
        if tok.type == TT.STRING:    self.advance(); return JStringLiteralNode(tok.value)
        if tok.value == 'true':      self.advance(); return JBoolLiteralNode('true')
        if tok.value == 'false':     self.advance(); return JBoolLiteralNode('false')

        if tok.type == TT.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TT.RPAREN)
            return expr

        if tok.type == TT.ID:
            name = self.advance().value

            # map.get(key) or map.containsKey(key)
            if self.match(TT.DOT):
                self.advance()
                method = self.expect(TT.ID).value
                self.expect(TT.LPAREN)
                key = self.parse_expression()
                self.expect(TT.RPAREN)
                if method == 'get':         return JMapGetNode(name, key)
                if method == 'containsKey': return JMapContainsNode(name, key)
                return JMethodCallExprNode(f'{name}.{method}', [key])

            # 2D array access: m[i][j]
            if self.match(TT.LBRACK) and self.peek(2).type == TT.RBRACK \
                    and self.peek(3).type == TT.LBRACK:
                self.advance()
                row = self.parse_expression()
                self.expect(TT.RBRACK)
                self.advance()
                col = self.parse_expression()
                self.expect(TT.RBRACK)
                return JArray2DAccessNode(name, row, col)

            # 1D array access: arr[i]
            if self.match(TT.LBRACK):
                self.advance()
                index = self.parse_expression()
                self.expect(TT.RBRACK)
                return JArrayAccessNode(name, index)

            # Function call: func(args)
            if self.match(TT.LPAREN):
                self.advance()
                args = []
                if not self.match(TT.RPAREN):
                    args.append(self.parse_expression())
                    while self.match(TT.COMMA):
                        self.advance()
                        args.append(self.parse_expression())
                self.expect(TT.RPAREN)
                return JMethodCallExprNode(name, args)

            return JIDNode(name)

        raise SyntaxError(f'[JavaParser] Line {tok.line}: Unexpected: {tok.value!r}')
