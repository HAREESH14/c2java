# ─────────────────────────────────────────────────────────────────────────────
#  lexer.py
#  Tokenizes C source code into a list of Token objects.
#  No external libraries required — pure Python.
# ─────────────────────────────────────────────────────────────────────────────

import re

# ── Token types ───────────────────────────────────────────────────────────────
class TT:
    # Literals
    INT_LIT   = 'INT_LIT'
    FLOAT_LIT = 'FLOAT_LIT'
    CHAR_LIT  = 'CHAR_LIT'
    STRING    = 'STRING'
    ID        = 'ID'
    DEFINE    = 'DEFINE'    # #define NAME VALUE — value is a (name, value_str) tuple


    # Keywords — types
    INT      = 'int'
    FLOAT    = 'float'
    DOUBLE   = 'double'
    CHAR     = 'char'
    VOID     = 'void'
    LONG     = 'long'
    SHORT    = 'short'
    UNSIGNED = 'unsigned'
    BOOL     = 'bool'

    # Keywords — control flow
    IF       = 'if'
    ELSE     = 'else'
    FOR      = 'for'
    WHILE    = 'while'
    DO       = 'do'
    RETURN   = 'return'
    BREAK    = 'break'
    CONTINUE = 'continue'
    SWITCH   = 'switch'
    CASE     = 'case'
    DEFAULT  = 'default'

    # Keywords — I/O
    PRINTF = 'printf'
    SCANF  = 'scanf'

    # Arithmetic operators
    PLUS   = '+'
    MINUS  = '-'
    STAR   = '*'
    SLASH  = '/'
    MOD    = '%'

    # Comparison operators
    EQ  = '=='
    NEQ = '!='
    LT  = '<'
    GT  = '>'
    LTE = '<='
    GTE = '>='

    # Logical operators
    AND = '&&'
    OR  = '||'
    NOT = '!'

    # Assignment operators
    ASSIGN  = '='
    PLUSEQ  = '+='
    MINUSEQ = '-='
    STAREQ  = '*='
    SLASHEQ = '/='
    MODEQ   = '%='

    # Increment / decrement
    INC = '++'
    DEC = '--'

    # Bitwise operators
    BITAND = '&'
    BITOR  = '|'
    BITXOR = '^'
    BITNOT = '~'
    LSHIFT = '<<'
    RSHIFT = '>>'

    # Ternary
    QUESTION = '?'
    COLON    = ':'

    # Delimiters
    LPAREN = '('
    RPAREN = ')'
    LBRACE = '{'
    RBRACE = '}'
    LBRACK = '['
    RBRACK = ']'
    SEMI   = ';'
    COMMA  = ','

    EOF = 'EOF'


KEYWORDS = {
    # Types
    'int', 'float', 'double', 'char', 'void',
    'long', 'short', 'unsigned', 'bool',
    # Control
    'if', 'else', 'for', 'while', 'do', 'return',
    'break', 'continue', 'switch', 'case', 'default',
    # I/O
    'printf', 'scanf',
}


class Token:
    def __init__(self, type_, value, line=0):
        self.type  = type_
        self.value = value
        self.line  = line

    def __repr__(self):
        return f'Token({self.type}, {self.value!r}, line={self.line})'


class Lexer:
    def __init__(self, source):
        self.source = source
        self.pos    = 0
        self.line   = 1
        self.tokens = []

    def error(self, msg):
        raise SyntaxError(f'[Lexer] Line {self.line}: {msg}')

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

            # Whitespace
            if ch in ' \t\r\n':
                self.advance()

            # Preprocessor directive
            elif ch == '#':
                # Read the directive word (include, define, pragma, etc.)
                self.advance()  # consume '#'
                directive = ''
                while self.pos < len(self.source) and self.peek().isalpha():
                    directive += self.advance()
                if directive == 'define':
                    # Skip whitespace between 'define' and name
                    while self.pos < len(self.source) and self.peek() in ' \t':
                        self.advance()
                    # Read macro name
                    name = ''
                    while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == '_'):
                        name += self.advance()
                    # Skip whitespace between name and value
                    while self.pos < len(self.source) and self.peek() in ' \t':
                        self.advance()
                    # Read value (rest of line)
                    value = ''
                    while self.pos < len(self.source) and self.peek() != '\n':
                        value += self.advance()
                    # Emit a DEFINE token carrying (name, value.strip())
                    self.tokens.append(Token(TT.DEFINE, (name, value.strip()), self.line))
                else:
                    # #include, #pragma, etc. — skip rest of line
                    while self.pos < len(self.source) and self.peek() != '\n':
                        self.advance()


            # Line comment  //
            elif ch == '/' and self.peek(1) == '/':
                while self.pos < len(self.source) and self.peek() != '\n':
                    self.advance()

            # Block comment  /* ... */
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
        """Read a double-quoted string literal."""
        self.advance()  # consume opening "
        result = '"'
        while self.pos < len(self.source) and self.peek() != '"':
            if self.peek() == '\\':
                result += self.advance()   # backslash
            result += self.advance()
        self.advance()  # consume closing "
        result += '"'
        return result

    def read_char(self):
        """Read a single-quoted char literal."""
        self.advance()  # consume '
        result = "'"
        if self.peek() == '\\':
            result += self.advance()
        result += self.advance()
        self.advance()  # consume closing '
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

            # ── String literal ────────────────────────────────────────────
            if ch == '"':
                val = self.read_string()
                self.tokens.append(Token(TT.STRING, val, line))
                continue

            # ── Char literal ──────────────────────────────────────────────
            if ch == "'":
                val = self.read_char()
                self.tokens.append(Token(TT.CHAR_LIT, val, line))
                continue

            # ── Number literals ───────────────────────────────────────────
            if ch.isdigit() or (ch == '.' and self.peek(1).isdigit()):
                num = ''
                is_float = False
                while self.pos < len(self.source) and (self.peek().isdigit() or self.peek() == '.'):
                    if self.peek() == '.':
                        is_float = True
                    num += self.advance()
                # consume optional f/F/l/L suffix
                if self.peek() in ('f', 'F', 'l', 'L'):
                    self.advance()
                    is_float = True
                tt = TT.FLOAT_LIT if is_float else TT.INT_LIT
                self.tokens.append(Token(tt, num, line))
                continue

            # ── Identifiers and keywords ──────────────────────────────────
            if ch.isalpha() or ch == '_':
                word = ''
                while self.pos < len(self.source) and (self.peek().isalnum() or self.peek() == '_'):
                    word += self.advance()
                tt = word if word in KEYWORDS else TT.ID
                self.tokens.append(Token(tt, word, line))
                continue

            # ── Three-character operators (must check before two-char) ─────
            three = ch + self.peek(1) + self.peek(2)
            # (none currently needed, placeholder for future)

            # ── Two-character operators ───────────────────────────────────
            two = ch + self.peek(1)
            if two == '++':  self.advance(); self.advance(); self.tokens.append(Token(TT.INC,    '++', line)); continue
            if two == '--':  self.advance(); self.advance(); self.tokens.append(Token(TT.DEC,    '--', line)); continue
            if two == '==':  self.advance(); self.advance(); self.tokens.append(Token(TT.EQ,     '==', line)); continue
            if two == '!=':  self.advance(); self.advance(); self.tokens.append(Token(TT.NEQ,    '!=', line)); continue
            if two == '<=':  self.advance(); self.advance(); self.tokens.append(Token(TT.LTE,    '<=', line)); continue
            if two == '>=':  self.advance(); self.advance(); self.tokens.append(Token(TT.GTE,    '>=', line)); continue
            if two == '&&':  self.advance(); self.advance(); self.tokens.append(Token(TT.AND,    '&&', line)); continue
            if two == '||':  self.advance(); self.advance(); self.tokens.append(Token(TT.OR,     '||', line)); continue
            if two == '+=':  self.advance(); self.advance(); self.tokens.append(Token(TT.PLUSEQ, '+=', line)); continue
            if two == '-=':  self.advance(); self.advance(); self.tokens.append(Token(TT.MINUSEQ,'-=', line)); continue
            if two == '*=':  self.advance(); self.advance(); self.tokens.append(Token(TT.STAREQ, '*=', line)); continue
            if two == '/=':  self.advance(); self.advance(); self.tokens.append(Token(TT.SLASHEQ,'/=', line)); continue
            if two == '%=':  self.advance(); self.advance(); self.tokens.append(Token(TT.MODEQ,  '%=', line)); continue
            if two == '<<':  self.advance(); self.advance(); self.tokens.append(Token(TT.LSHIFT, '<<', line)); continue
            if two == '>>':  self.advance(); self.advance(); self.tokens.append(Token(TT.RSHIFT, '>>', line)); continue

            # ── Single-character tokens ───────────────────────────────────
            single_map = {
                '+': TT.PLUS,  '-': TT.MINUS,  '*': TT.STAR,   '/': TT.SLASH,
                '%': TT.MOD,   '<': TT.LT,     '>': TT.GT,     '!': TT.NOT,
                '=': TT.ASSIGN,
                '&': TT.BITAND, '|': TT.BITOR, '^': TT.BITXOR, '~': TT.BITNOT,
                '?': TT.QUESTION, ':': TT.COLON,
                '(': TT.LPAREN, ')': TT.RPAREN,
                '{': TT.LBRACE, '}': TT.RBRACE,
                '[': TT.LBRACK, ']': TT.RBRACK,
                ';': TT.SEMI,   ',': TT.COMMA,
            }
            if ch in single_map:
                self.advance()
                self.tokens.append(Token(single_map[ch], ch, line))
                continue

            self.error(f"Unknown character: '{ch}'")

        return self.tokens
