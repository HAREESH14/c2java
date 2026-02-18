# ─────────────────────────────────────────────────────────────────────────────
#  parser.py
#  Recursive Descent Parser.
#  Consumes the token list from the Lexer and builds an AST.
# ─────────────────────────────────────────────────────────────────────────────

from lexer import TT, Token
from ast_nodes import *

TYPES = {TT.INT, TT.FLOAT, TT.DOUBLE, TT.CHAR, TT.VOID}


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
            self.expect(TT.RBRACK)
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

        # if statement
        if cur.type == TT.IF:
            return self.parse_if()

        # for loop
        if cur.type == TT.FOR:
            return self.parse_for()

        # while loop
        if cur.type == TT.WHILE:
            return self.parse_while()

        # do-while
        if cur.type == TT.DO:
            return self.parse_do_while()

        # printf
        if cur.type == TT.PRINTF:
            return self.parse_printf()

        # return
        if cur.type == TT.RETURN:
            return self.parse_return()

        # ID-starting statements: assignment, array assignment, function call
        if cur.type == TT.ID:
            return self.parse_id_statement()

        raise SyntaxError(f'[Parser] Line {cur.line}: Unexpected token {cur.value!r}')

    # ── Declaration (var or array) ────────────────────────────────────────────
    def parse_declaration(self):
        type_    = self.expect_type()
        name     = self.expect(TT.ID).value

        # 2D array:  int m[3][3];
        if self.match(TT.LBRACK) and self.peek(2).type == TT.RBRACK and \
           self.peek(3).type == TT.LBRACK:
            self.advance()                          # [
            rows = self.expect(TT.INT_LIT).value
            self.expect(TT.RBRACK)                  # ]
            self.advance()                          # [
            cols = self.expect(TT.INT_LIT).value
            self.expect(TT.RBRACK)                  # ]
            self.expect(TT.SEMI)
            return ArrayDecl2DNode(type_, name, rows, cols)

        # 1D array with size:  int arr[5];
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

    # ── ID-starting statements ────────────────────────────────────────────────
    def parse_id_statement(self):
        name = self.expect(TT.ID).value

        # 2D array assignment:  m[i][j] = expr;
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

        if op == TT.INC:
            self.advance()
            return UpdateNode(name, '++')
        if op == TT.DEC:
            self.advance()
            return UpdateNode(name, '--')
        if op == TT.PLUSEQ:
            self.advance()
            val = self.parse_expression()
            return UpdateNode(name, '+=', val)
        if op == TT.MINUSEQ:
            self.advance()
            val = self.parse_expression()
            return UpdateNode(name, '-=', val)
        if op == TT.ASSIGN:
            self.advance()
            val = self.parse_expression()
            return UpdateNode(name, '=', val)

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
    # Precedence (low → high):  || → && → == != → < > <= >= → + - → * / % → unary → primary

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.match(TT.OR):
            op = self.advance().value
            right = self.parse_and()
            left = BinOpNode(left, op, right)
        return left

    def parse_and(self):
        left = self.parse_equality()
        while self.match(TT.AND):
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
        left = self.parse_additive()
        while self.match(TT.LT, TT.GT, TT.LTE, TT.GTE):
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
        return self.parse_primary()

    def parse_primary(self):
        tok = self.current()

        # Integer literal
        if tok.type == TT.INT_LIT:
            self.advance()
            return IntLiteralNode(tok.value)

        # Float literal
        if tok.type == TT.FLOAT_LIT:
            self.advance()
            return FloatLiteralNode(tok.value)

        # Char literal
        if tok.type == TT.CHAR_LIT:
            self.advance()
            return CharLiteralNode(tok.value)

        # String literal
        if tok.type == TT.STRING:
            self.advance()
            return StringLiteralNode(tok.value)

        # Parenthesised expression
        if tok.type == TT.LPAREN:
            self.advance()
            expr = self.parse_expression()
            self.expect(TT.RPAREN)
            return expr

        # ID — could be: variable, array access, 2D array access, function call
        if tok.type == TT.ID:
            name = self.advance().value

            # 2D array access:  m[i][j]
            if self.match(TT.LBRACK) and self.peek(2).type == TT.RBRACK \
                    and self.peek(3).type == TT.LBRACK:
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
