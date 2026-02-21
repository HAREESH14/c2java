# ─────────────────────────────────────────────────────────────────────────────
#  java_lexer.py
#  Tokenizes Java source code.
#  External library used: NONE (pure Python)
# ─────────────────────────────────────────────────────────────────────────────

class TT:
    # Literals
    INT_LIT   = 'INT_LIT'
    FLOAT_LIT = 'FLOAT_LIT'
    CHAR_LIT  = 'CHAR_LIT'
    STRING    = 'STRING'
    ID        = 'ID'

    # Java keywords
    PUBLIC    = 'public'
    PRIVATE   = 'private'
    STATIC    = 'static'
    VOID      = 'void'
    INT       = 'int'
    FLOAT     = 'float'
    DOUBLE    = 'double'
    CHAR      = 'char'
    BOOLEAN   = 'boolean'
    CLASS     = 'class'
    IF        = 'if'
    ELSE      = 'else'
    FOR       = 'for'
    WHILE     = 'while'
    DO        = 'do'
    RETURN    = 'return'
    NEW       = 'new'
    TRUE      = 'true'
    FALSE     = 'false'
    IMPORT    = 'import'
    HASHMAP   = 'HashMap'

    # Operators
    PLUS    = '+'
    MINUS   = '-'
    STAR    = '*'
    SLASH   = '/'
    MOD     = '%'
    EQ      = '=='
    NEQ     = '!='
    LT      = '<'
    GT      = '>'
    LTE     = '<='
    GTE     = '>='
    AND     = '&&'
    OR      = '||'
    NOT     = '!'
    ASSIGN  = '='
    PLUSEQ  = '+='
    MINUSEQ = '-='
    INC     = '++'
    DEC     = '--'

    # Delimiters
    LPAREN  = '('
    RPAREN  = ')'
    LBRACE  = '{'
    RBRACE  = '}'
    LBRACK  = '['
    RBRACK  = ']'
    SEMI    = ';'
    COMMA   = ','
    DOT     = '.'

    EOF     = 'EOF'


KEYWORDS = {
    'public', 'private', 'static', 'void',
    'int', 'float', 'double', 'char', 'boolean',
    'class', 'if', 'else', 'for', 'while', 'do',
    'return', 'new', 'true', 'false', 'import', 'HashMap',
    'String', 'System'
}


class Token:
    def __init__(self, type_, value, line=0):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return f'Token({self.type}, {self.value!r})'


class JavaLexer:
    def __init__(self, source):
        self.source = source
        self.pos    = 0
        self.line   = 1
        self.tokens = []

    def error(self, msg):
        raise SyntaxError(f'[JavaLexer] Line {self.line}: {msg}')

    def peek(self, offset=0):
        i = self.pos + offset
        return self.source[i] if i < len(self.source) else '\0'

    def advance(self):
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
        return ch

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.peek()
            if ch in ' \t\r\n':
                self.advance()
            elif ch == '/' and self.peek(1) == '/':
                while self.pos < len(self.source) and self.peek() != '\n':
                    self.advance()
            elif ch == '/' and self.peek(1) == '*':
                self.advance(); self.advance()
                while self.pos < len(self.source):
                    if self.peek() == '*' and self.peek(1) == '/':
                        self.advance(); self.advance()
                        break
                    self.advance()
            else:
                break

    def read_string(self):
        self.advance()  # opening "
        result = '"'
        while self.pos < len(self.source) and self.peek() != '"':
            if self.peek() == '\\':
                result += self.advance()
            result += self.advance()
        self.advance()  # closing "
        result += '"'
        return result

    def read_char(self):
        self.advance()  # opening '
        result = "'"
        if self.peek() == '\\':
            result += self.advance()
        result += self.advance()
        self.advance()  # closing '
        result += "'"
        return result

    def tokenize(self):
        while True:
            self.skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                self.tokens.append(Token(TT.EOF, 'EOF', self.line))
                break

            line = self.line
            ch   = self.peek()

            if ch == '"':
                val = self.read_string()
                self.tokens.append(Token(TT.STRING, val, line))
                continue

            if ch == "'":
                val = self.read_char()
                self.tokens.append(Token(TT.CHAR_LIT, val, line))
                continue

            if ch.isdigit() or (ch == '.' and self.peek(1).isdigit()):
                num = ''
                is_float = False
                while self.pos < len(self.source) and (self.peek().isdigit() or self.peek() in '.fF'):
                    if self.peek() in '.': is_float = True
                    if self.peek() in 'fF':
                        self.advance()  # skip f suffix
                        break
                    num += self.advance()
                tt = TT.FLOAT_LIT if is_float else TT.INT_LIT
                self.tokens.append(Token(tt, num, line))
                continue

            if ch.isalpha() or ch == '_':
                word = ''
                while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == '_'):
                    word += self.advance()
                tt = word if word in KEYWORDS else TT.ID
                self.tokens.append(Token(tt, word, line))
                continue

            # Two-character operators
            two = ch + self.peek(1)
            two_map = {
                '++': TT.INC, '--': TT.DEC, '==': TT.EQ, '!=': TT.NEQ,
                '<=': TT.LTE, '>=': TT.GTE, '&&': TT.AND, '||': TT.OR,
                '+=': TT.PLUSEQ, '-=': TT.MINUSEQ
            }
            if two in two_map:
                self.advance(); self.advance()
                self.tokens.append(Token(two_map[two], two, line))
                continue

            single_map = {
                '+': TT.PLUS, '-': TT.MINUS, '*': TT.STAR, '/': TT.SLASH,
                '%': TT.MOD, '<': TT.LT, '>': TT.GT, '!': TT.NOT,
                '=': TT.ASSIGN, '(': TT.LPAREN, ')': TT.RPAREN,
                '{': TT.LBRACE, '}': TT.RBRACE, '[': TT.LBRACK,
                ']': TT.RBRACK, ';': TT.SEMI, ',': TT.COMMA, '.': TT.DOT,
            }
            if ch in single_map:
                self.advance()
                self.tokens.append(Token(single_map[ch], ch, line))
                continue

            self.error(f"Unknown character: '{ch}'")

        return self.tokens
