# ─────────────────────────────────────────────────────────────────────────────
#  parser.py
#  Recursive Descent Parser.
#  Consumes the token list from the Lexer and builds an AST.
# ─────────────────────────────────────────────────────────────────────────────

from lexer import TT, Token
from ast_nodes import *

TYPES = {TT.INT, TT.FLOAT, TT.DOUBLE, TT.CHAR, TT.VOID,
         TT.LONG, TT.SHORT, TT.UNSIGNED, TT.BOOL}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos    = 0

    # ── Token navigation ──────────────────────────────────────────────────────
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
                f'[Parser] Line {tok.line}: Expected {type_!r} but got {tok.type!r} ({tok.value!r})'
            )
        return self.advance()

    def match(self, *types):
        return self.current().type in types

    # ── Program ───────────────────────────────────────────────────────────────
    def parse(self):
        functions = []
        while not self.match(TT.EOF):
            functions.append(self.parse_function())
        return ProgramNode(functions)

    # ── Function declaration ──────────────────────────────────────────────────
    def parse_function(self):
        ret_type = self.expect_type()
        name_tok = self.expect(TT.ID)
        name     = name_tok.value
        is_main  = (name == 'main')

        self.expect(TT.LPAREN)
        params = []
        if not self.match(TT.RPAREN):
            params = self.parse_param_list()
        self.expect(TT.RPAREN)
        body = self.parse_block()

        return FunctionNode(ret_type, name, params, body, is_main)

    def expect_type(self):
        tok = self.current()
        if tok.type not in TYPES:
            raise SyntaxError(f'[Parser] Line {tok.line}: Expected a type, got {tok.value!r}')
        return self.advance().value

    def parse_param_list(self):
        params = [self.parse_param()]
        while self.match(TT.COMMA):
            self.advance()
            params.append(self.parse_param())
        return params

    def parse_param(self):
        type_  = self.expect_type()
        name   = self.expect(TT.ID).value
        is_arr = False
        if self.match(TT.LBRACK):
            self.advance()
            if self.match(TT.RBRACK):
                self.advance()
            is_arr = True
        return ParamNode(type_, name, is_arr)

    # ── Block ─────────────────────────────────────────────────────────────────
    def parse_block(self):
        self.expect(TT.LBRACE)
        stmts = []
        while not self.match(TT.RBRACE) and not self.match(TT.EOF):
            stmts.append(self.parse_statement())
        self.expect(TT.RBRACE)
        return BlockNode(stmts)

    # ── Statement dispatcher ──────────────────────────────────────────────────
    def parse_statement(self):
        cur = self.current()

        # Variable / array declaration: starts with a type keyword
        if cur.type in TYPES:
            return self.parse_declaration()

        if cur.type == TT.IF:       return self.parse_if()
        if cur.type == TT.FOR:      return self.parse_for()
        if cur.type == TT.WHILE:    return self.parse_while()
        if cur.type == TT.DO:       return self.parse_do_while()
        if cur.type == TT.SWITCH:   return self.parse_switch()
        if cur.type == TT.PRINTF:   return self.parse_printf()
        if cur.type == TT.SCANF:    return self.parse_scanf()
        if cur.type == TT.RETURN:   return self.parse_return()
        if cur.type == TT.BREAK:    return self.parse_break()
        if cur.type == TT.CONTINUE: return self.parse_continue()

        # ID-starting statements: assignment, compound assign, array assign, function call
        if cur.type == TT.ID:
            return self.parse_id_statement()

        raise SyntaxError(f'[Parser] Line {cur.line}: Unexpected token {cur.value!r}')

    # ── Declaration (var or array) ────────────────────────────────────────────
    def parse_declaration(self):
        type_ = self.expect_type()
        name  = self.expect(TT.ID).value

        # ── Bug 2 Fix: use _is_2d_array() instead of fragile peek offsets ──
        if self.match(TT.LBRACK) and self._is_2d_array():
            # 2D array:  int m[rows][cols];
            self.advance()                          # [
            rows = self.expect(TT.INT_LIT).value
            self.expect(TT.RBRACK)                  # ]
            self.advance()                          # [
            cols = self.expect(TT.INT_LIT).value
            self.expect(TT.RBRACK)                  # ]
            self.expect(TT.SEMI)
            return ArrayDecl2DNode(type_, name, rows, cols)

        # 1D array with size:  int arr[5];   OR  int arr[] = {...};
        if self.match(TT.LBRACK):
            self.advance()   # [
            size = None
            if self.match(TT.INT_LIT):
                size = self.advance().value
            self.expect(TT.RBRACK)   # ]

            init_values = None
            if self.match(TT.ASSIGN):
                self.advance()
                self.expect(TT.LBRACE)
                init_values = [self.parse_expression()]
                while self.match(TT.COMMA):
                    self.advance()
                    init_values.append(self.parse_expression())
                self.expect(TT.RBRACE)

            self.expect(TT.SEMI)
            return ArrayDeclNode(type_, name, size, init_values)

        # Simple variable:  int x = 5;   OR   int x;
        initializer = None
        if self.match(TT.ASSIGN):
            self.advance()
            initializer = self.parse_expression()
        self.expect(TT.SEMI)
        return VarDeclNode(type_, name, initializer)

    def _is_2d_array(self):
        """
        Bug 2 Fix: Scan ahead to determine if this is a 2D array declaration.
        We are currently sitting on '['. A 2D array looks like [INT_LIT][INT_LIT].
        We scan forward past the first bracket group and check if another '[' follows.
        This correctly handles any expression inside the first bracket.
        """
        depth = 0
        i = self.pos
        while i < len(self.tokens):
            tt = self.tokens[i].type
            if tt == TT.LBRACK:
                depth += 1
            elif tt == TT.RBRACK:
                depth -= 1
                if depth == 0:
                    # Check if the very next token is another '['
                    next_i = i + 1
                    if next_i < len(self.tokens) and self.tokens[next_i].type == TT.LBRACK:
                        return True
                    return False
            elif tt == TT.EOF:
                return False
            i += 1
        return False

    # ── ID-starting statements ────────────────────────────────────────────────
    def parse_id_statement(self):
        name = self.expect(TT.ID).value

        # ── Bug 2 Fix: use _is_2d_array() for assignment too ──
        if self.match(TT.LBRACK) and self._is_2d_array():
            # 2D array assignment:  m[expr][expr] = expr;
            self.advance()
            row = self.parse_expression()
            self.expect(TT.RBRACK)
            self.advance()
            col = self.parse_expression()
            self.expect(TT.RBRACK)
            self.expect(TT.ASSIGN)
            val = self.parse_expression()
            self.expect(TT.SEMI)
            return ArrayAssign2DNode(name, row, col, val)

        # 1D array assignment:  arr[i] = expr;
        if self.match(TT.LBRACK):
            self.advance()
            index = self.parse_expression()
            self.expect(TT.RBRACK)
            self.expect(TT.ASSIGN)
            value = self.parse_expression()
            self.expect(TT.SEMI)
            return ArrayAssignNode(name, index, value)

        # Function call statement:  myFunc(a, b);
        if self.match(TT.LPAREN):
            self.advance()
            args = []
            if not self.match(TT.RPAREN):
                args = self.parse_arg_list()
            self.expect(TT.RPAREN)
            self.expect(TT.SEMI)
            return FuncCallStmtNode(name, args)

        # ── Bug 5 Fix: compound assignment operators as statements ──
        COMPOUND_OPS = {TT.PLUSEQ, TT.MINUSEQ, TT.STAREQ, TT.SLASHEQ, TT.MODEQ}
        if self.current().type in COMPOUND_OPS:
            op = self.advance().value
            value = self.parse_expression()
            self.expect(TT.SEMI)
            return CompoundAssignNode(name, op, value)

        # Simple assignment:  x = expr;
        self.expect(TT.ASSIGN)
        value = self.parse_expression()
        self.expect(TT.SEMI)
        return AssignNode(name, value)

    # ── if / else if / else ───────────────────────────────────────────────────
    def parse_if(self):
        self.expect(TT.IF)
        self.expect(TT.LPAREN)
        cond = self.parse_expression()
        self.expect(TT.RPAREN)
        body = self.parse_block()
        branches = [(cond, body)]

        else_block = None
        while self.match(TT.ELSE):
            self.advance()
            if self.match(TT.IF):
                self.advance()
                self.expect(TT.LPAREN)
                cond2 = self.parse_expression()
                self.expect(TT.RPAREN)
                body2 = self.parse_block()
                branches.append((cond2, body2))
            else:
                else_block = self.parse_block()
                break

        return IfNode(branches, else_block)

    # ── for loop ──────────────────────────────────────────────────────────────
    def parse_for(self):
        self.expect(TT.FOR)
        self.expect(TT.LPAREN)
        init = self.parse_for_init()
        self.expect(TT.SEMI)
        cond = self.parse_expression()
        self.expect(TT.SEMI)
        update = self.parse_for_update()
        self.expect(TT.RPAREN)
        body = self.parse_block()
        return ForNode(init, cond, update, body)

    def parse_for_init(self):
        # int i = 0  OR  i = 0
        if self.current().type in TYPES:
            type_ = self.expect_type()
            name  = self.expect(TT.ID).value
            self.expect(TT.ASSIGN)
            val   = self.parse_expression()
            return VarDeclNode(type_, name, val)
        else:
            name = self.expect(TT.ID).value
            self.expect(TT.ASSIGN)
            val  = self.parse_expression()
            return AssignNode(name, val)

    def parse_for_update(self):
        name = self.expect(TT.ID).value
        op   = self.current().type

        if op == TT.INC:     self.advance(); return UpdateNode(name, '++')
        if op == TT.DEC:     self.advance(); return UpdateNode(name, '--')
        if op == TT.PLUSEQ:  self.advance(); return UpdateNode(name, '+=', self.parse_expression())
        if op == TT.MINUSEQ: self.advance(); return UpdateNode(name, '-=', self.parse_expression())
        if op == TT.ASSIGN:  self.advance(); return UpdateNode(name, '=',  self.parse_expression())

        raise SyntaxError(f'[Parser] Bad for-update at {self.current().value!r}')

    # ── while loop ────────────────────────────────────────────────────────────
    def parse_while(self):
        self.expect(TT.WHILE)
        self.expect(TT.LPAREN)
        cond = self.parse_expression()
        self.expect(TT.RPAREN)
        body = self.parse_block()
        return WhileNode(cond, body)

    # ── do-while loop ─────────────────────────────────────────────────────────
    def parse_do_while(self):
        self.expect(TT.DO)
        body = self.parse_block()
        self.expect(TT.WHILE)
        self.expect(TT.LPAREN)
        cond = self.parse_expression()
        self.expect(TT.RPAREN)
        self.expect(TT.SEMI)
        return DoWhileNode(body, cond)

    # ── break ─────────────────────────────────────────────────────────────────
    def parse_break(self):
        self.expect(TT.BREAK)
        self.expect(TT.SEMI)
        return BreakNode()

    # ── continue ──────────────────────────────────────────────────────────────
    def parse_continue(self):
        self.expect(TT.CONTINUE)
        self.expect(TT.SEMI)
        return ContinueNode()

    # ── switch / case / default ───────────────────────────────────────────────
    def parse_switch(self):
        self.expect(TT.SWITCH)
        self.expect(TT.LPAREN)
        expr = self.parse_expression()
        self.expect(TT.RPAREN)
        self.expect(TT.LBRACE)

        cases = []
        while not self.match(TT.RBRACE) and not self.match(TT.EOF):
            if self.match(TT.CASE):
                cases.append(self.parse_case())
            elif self.match(TT.DEFAULT):
                cases.append(self.parse_default())
            else:
                raise SyntaxError(
                    f'[Parser] Line {self.current().line}: Expected case/default in switch, got {self.current().value!r}'
                )

        self.expect(TT.RBRACE)
        return SwitchNode(expr, cases)

    def parse_case(self):
        self.expect(TT.CASE)
        value = self.parse_primary()   # int or char literal
        self.expect(TT.COLON)
        stmts = []
        while not self.match(TT.CASE) and not self.match(TT.DEFAULT) \
                and not self.match(TT.RBRACE) and not self.match(TT.EOF):
            stmts.append(self.parse_statement())
        return CaseNode(value, stmts)

    def parse_default(self):
        self.expect(TT.DEFAULT)
        self.expect(TT.COLON)
        stmts = []
        while not self.match(TT.CASE) and not self.match(TT.DEFAULT) \
                and not self.match(TT.RBRACE) and not self.match(TT.EOF):
            stmts.append(self.parse_statement())
        return DefaultCaseNode(stmts)

    # ── printf ────────────────────────────────────────────────────────────────
    def parse_printf(self):
        self.expect(TT.PRINTF)
        self.expect(TT.LPAREN)
        fmt = self.expect(TT.STRING).value
        args = []
        while self.match(TT.COMMA):
            self.advance()
            args.append(self.parse_expression())
        self.expect(TT.RPAREN)
        self.expect(TT.SEMI)
        return PrintNode(fmt, args)

    # ── scanf ─────────────────────────────────────────────────────────────────
    def parse_scanf(self):
        self.expect(TT.SCANF)
        self.expect(TT.LPAREN)
        fmt = self.expect(TT.STRING).value
        vars_ = []
        while self.match(TT.COMMA):
            self.advance()
            # Strip the & address-of operator
            if self.match(TT.BITAND):
                self.advance()
            var_name = self.expect(TT.ID).value
            vars_.append(var_name)
        self.expect(TT.RPAREN)
        self.expect(TT.SEMI)
        return ScanfNode(fmt, vars_)

    # ── return ────────────────────────────────────────────────────────────────
    def parse_return(self):
        self.expect(TT.RETURN)
        value = None
        if not self.match(TT.SEMI):
            value = self.parse_expression()
        self.expect(TT.SEMI)
        return ReturnNode(value)

    # ── Argument list (for function calls) ───────────────────────────────────
    def parse_arg_list(self):
        args = [self.parse_expression()]
        while self.match(TT.COMMA):
            self.advance()
            args.append(self.parse_expression())
        return args

    # ── Expressions (with operator precedence) ────────────────────────────────
    # Precedence (low → high):
    #   ternary → || → && → | → ^ → & → == != → < > <= >= → << >> → + - → * / % → unary → primary

    def parse_expression(self):
        return self.parse_ternary()

    def parse_ternary(self):
        """Ternary operator:  cond ? then : else"""
        expr = self.parse_or()
        if self.match(TT.QUESTION):
            self.advance()
            then_expr = self.parse_expression()
            self.expect(TT.COLON)
            else_expr = self.parse_expression()
            return TernaryNode(expr, then_expr, else_expr)
        return expr

    def parse_or(self):
        left = self.parse_and()
        while self.match(TT.OR):
            op = self.advance().value
            right = self.parse_and()
            left = BinOpNode(left, op, right)
        return left

    def parse_and(self):
        left = self.parse_bitor()
        while self.match(TT.AND):
            op = self.advance().value
            right = self.parse_bitor()
            left = BinOpNode(left, op, right)
        return left

    def parse_bitor(self):
        left = self.parse_bitxor()
        while self.match(TT.BITOR):
            op = self.advance().value
            right = self.parse_bitxor()
            left = BinOpNode(left, op, right)
        return left

    def parse_bitxor(self):
        left = self.parse_bitand()
        while self.match(TT.BITXOR):
            op = self.advance().value
            right = self.parse_bitand()
            left = BinOpNode(left, op, right)
        return left

    def parse_bitand(self):
        left = self.parse_equality()
        while self.match(TT.BITAND):
            op = self.advance().value
            right = self.parse_equality()
            left = BinOpNode(left, op, right)
        return left

    def parse_equality(self):
        left = self.parse_relational()
        while self.match(TT.EQ, TT.NEQ):
            op = self.advance().value
            right = self.parse_relational()
            left = BinOpNode(left, op, right)
        return left

    def parse_relational(self):
        left = self.parse_shift()
        while self.match(TT.LT, TT.GT, TT.LTE, TT.GTE):
            op = self.advance().value
            right = self.parse_shift()
            left = BinOpNode(left, op, right)
        return left

    def parse_shift(self):
        left = self.parse_additive()
        while self.match(TT.LSHIFT, TT.RSHIFT):
            op = self.advance().value
            right = self.parse_additive()
            left = BinOpNode(left, op, right)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.match(TT.PLUS, TT.MINUS):
            op = self.advance().value
            right = self.parse_multiplicative()
            left = BinOpNode(left, op, right)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.match(TT.STAR, TT.SLASH, TT.MOD):
            op = self.advance().value
            right = self.parse_unary()
            left = BinOpNode(left, op, right)
        return left

    def parse_unary(self):
        if self.match(TT.NOT):
            op = self.advance().value
            return UnaryOpNode(op, self.parse_unary())
        if self.match(TT.MINUS):
            op = self.advance().value
            return UnaryOpNode(op, self.parse_unary())
        if self.match(TT.BITNOT):
            op = self.advance().value
            return UnaryOpNode(op, self.parse_unary())
        return self.parse_primary()

    def parse_primary(self):
        tok = self.current()

        if tok.type == TT.INT_LIT:   self.advance(); return IntLiteralNode(tok.value)
        if tok.type == TT.FLOAT_LIT: self.advance(); return FloatLiteralNode(tok.value)
        if tok.type == TT.CHAR_LIT:  self.advance(); return CharLiteralNode(tok.value)
        if tok.type == TT.STRING:    self.advance(); return StringLiteralNode(tok.value)

        # Parenthesised expression
        if tok.type == TT.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TT.RPAREN)
            return expr

        # ID — could be: variable, array access, 2D array access, function call
        if tok.type == TT.ID:
            name = self.advance().value

            # ── Bug 2 Fix: use _is_2d_array() ──
            if self.match(TT.LBRACK) and self._is_2d_array():
                # 2D array access:  m[expr][expr]
                self.advance()
                row = self.parse_expression()
                self.expect(TT.RBRACK)
                self.advance()
                col = self.parse_expression()
                self.expect(TT.RBRACK)
                return ArrayAccess2DNode(name, row, col)

            # 1D array access:  arr[i]
            if self.match(TT.LBRACK):
                self.advance()
                index = self.parse_expression()
                self.expect(TT.RBRACK)
                return ArrayAccessNode(name, index)

            # Function call expression:  add(x, y)
            if self.match(TT.LPAREN):
                self.advance()
                args = []
                if not self.match(TT.RPAREN):
                    args = self.parse_arg_list()
                self.expect(TT.RPAREN)
                return FuncCallExprNode(name, args)

            return IDNode(name)

        raise SyntaxError(
            f'[Parser] Line {tok.line}: Unexpected token in expression: {tok.value!r}'
        )
