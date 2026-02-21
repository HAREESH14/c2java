# ─────────────────────────────────────────────────────────────────────────────
#  java_to_c.py
#  Java → C translator using javalang (external AST library).
#
#  Key difference from a hand-written parser:
#    • javalang.parse.parse() does ALL the lexing and parsing.
#    • We receive a CompilationUnit with typed AST nodes.
#    • We walk the tree manually (javalang has no NodeVisitor base class),
#      dispatching on isinstance() checks.
#
#  javalang AST node types used:
#    CompilationUnit        → top-level
#    ClassDeclaration       → class Main { ... }
#    MethodDeclaration      → method → C function
#    FormalParameter        → method parameter
#    LocalVariableDeclaration → local variable
#    IfStatement            → if/else
#    ForStatement           → for loop
#    WhileStatement         → while loop
#    DoStatement            → do-while loop
#    ReturnStatement        → return
#    StatementExpression    → expression used as statement
#    MethodInvocation       → function call
#    BinaryOperation        → binary expression
#    MemberReference        → variable / field reference
#    Literal                → constant value
#    Assignment             → assignment expression
#    ArrayCreator           → new int[5]
#    ArrayInitializer       → {1, 2, 3}
# ─────────────────────────────────────────────────────────────────────────────

import javalang


# ── Type mapping ──────────────────────────────────────────────────────────────
JAVA_TO_C_TYPE = {
    'int':     'int',
    'float':   'float',
    'double':  'double',
    'char':    'char',
    'void':    'void',
    'long':    'long',
    'short':   'short',
    'boolean': 'int',    # no bool in C89; use int
    'String':  'char*',
    'boolean': 'int',
}

# Java System.out.* → C printf
PRINT_METHODS = {'printf', 'println', 'print', 'printf'}

# Java Math.* → C math.h
MATH_MAP = {
    'sqrt': 'sqrt', 'abs': 'abs', 'pow': 'pow',
    'ceil': 'ceil', 'floor': 'floor', 'round': 'round',
    'log': 'log', 'log10': 'log10',
    'sin': 'sin', 'cos': 'cos', 'tan': 'tan',
}

# Java Integer/Double/Long parse → C atoi/atof/atol
PARSE_MAP = {
    ('Integer', 'parseInt'):    'atoi',
    ('Double',  'parseDouble'): 'atof',
    ('Long',    'parseLong'):   'atol',
}

# Java Character.* → C ctype.h
CHAR_MAP = {
    'toUpperCase':  'toupper',
    'toLowerCase':  'tolower',
    'isLetter':     'isalpha',
    'isDigit':      'isdigit',
    'isWhitespace': 'isspace',
    'isUpperCase':  'isupper',
    'isLowerCase':  'islower',
}


def translate_type(java_type):
    """Map a Java type string to its C equivalent."""
    return JAVA_TO_C_TYPE.get(java_type, java_type)


# ── Main translator class ─────────────────────────────────────────────────────
class JavaToCTranslator:
    """
    Walks a javalang AST and emits C source code.

    javalang does NOT provide a NodeVisitor base class, so we use
    isinstance() dispatch throughout.
    """

    def __init__(self):
        self.indent_level = 0
        self.output       = []
        self.needs_stdio  = False
        self.needs_string = False
        self.needs_math   = False
        self.is_main      = False

    # ── Helpers ───────────────────────────────────────────────────────────────
    def ind(self):
        return '    ' * self.indent_level

    def emit(self, line):
        self.output.append(self.ind() + line)

    def emit_blank(self):
        self.output.append('')

    def result(self):
        return '\n'.join(self.output)

    # ── Top-level ─────────────────────────────────────────────────────────────
    def translate(self, source):
        """Parse Java source and return C source string."""
        tree = javalang.parse.parse(source)
        self._translate_compilation_unit(tree)
        return self.result()

    def _translate_compilation_unit(self, unit):
        """
        javalang CompilationUnit has:
          .types  → list of TypeDeclaration (ClassDeclaration, etc.)
        """
        # Collect all methods first to decide which headers to include
        methods = []
        for type_decl in unit.types:
            if isinstance(type_decl, javalang.tree.ClassDeclaration):
                for member in type_decl.body:
                    if isinstance(member, javalang.tree.MethodDeclaration):
                        methods.append(member)

        # Detect which headers are needed
        self._detect_headers(unit)

        # Emit headers
        if self.needs_stdio:
            self.emit('#include <stdio.h>')
        if self.needs_string:
            self.emit('#include <string.h>')
        if self.needs_math:
            self.emit('#include <math.h>')
        self.emit_blank()

        # Forward declarations (non-main functions first)
        non_main = [m for m in methods if m.name != 'main']
        for m in non_main:
            self.emit(self._func_signature(m) + ';')
        if non_main:
            self.emit_blank()

        # Emit functions (non-main first, then main)
        main_method = None
        for m in methods:
            if m.name == 'main':
                main_method = m
            else:
                self._translate_method(m)
                self.emit_blank()

        if main_method:
            self._translate_method(main_method)

    def _detect_headers(self, unit):
        """Walk the AST text to decide which #includes are needed."""
        src = str(unit)
        if 'printf' in src or 'println' in src or 'scanf' in src:
            self.needs_stdio = True
        if 'strlen' in src or 'strcmp' in src or 'strcpy' in src:
            self.needs_string = True
        if 'Math.' in src or 'sqrt' in src or 'pow' in src:
            self.needs_math = True

    # ── Method → C function ───────────────────────────────────────────────────
    def _func_signature(self, method):
        """Build the C function signature string."""
        ret_type = translate_type(method.return_type.name if method.return_type else 'void')
        name     = method.name

        if name == 'main':
            return 'int main()'

        params = []
        for p in (method.parameters or []):
            ctype = translate_type(p.type.name)
            pname = p.name
            if p.varargs:
                params.append('...')
            elif hasattr(p.type, 'dimensions') and p.type.dimensions:
                params.append(f'{ctype} {pname}[]')
            else:
                params.append(f'{ctype} {pname}')
        return f'{ret_type} {name}({", ".join(params)})'

    def _translate_method(self, method):
        self.is_main = (method.name == 'main')
        sig = self._func_signature(method)
        self.emit(sig + ' {')
        self.indent_level += 1
        for stmt in (method.body or []):
            self._translate_stmt(stmt)
        if self.is_main:
            self.emit('return 0;')
        self.indent_level -= 1
        self.emit('}')

    # ── Statement dispatcher ──────────────────────────────────────────────────
    def _translate_stmt(self, stmt):
        if isinstance(stmt, javalang.tree.LocalVariableDeclaration):
            self._translate_local_var(stmt)
        elif isinstance(stmt, javalang.tree.IfStatement):
            self._translate_if(stmt)
        elif isinstance(stmt, javalang.tree.ForStatement):
            self._translate_for(stmt)
        elif isinstance(stmt, javalang.tree.WhileStatement):
            self._translate_while(stmt)
        elif isinstance(stmt, javalang.tree.DoStatement):
            self._translate_do_while(stmt)
        elif isinstance(stmt, javalang.tree.ReturnStatement):
            self._translate_return(stmt)
        elif isinstance(stmt, javalang.tree.StatementExpression):
            self._translate_stmt_expr(stmt.expression)
        elif isinstance(stmt, javalang.tree.BreakStatement):
            self.emit('break;')
        elif isinstance(stmt, javalang.tree.ContinueStatement):
            self.emit('continue;')
        elif isinstance(stmt, javalang.tree.BlockStatement):
            for s in stmt.statements:
                self._translate_stmt(s)
        else:
            self.emit(f'/* unsupported: {type(stmt).__name__} */')

    # ── Local variable declaration ────────────────────────────────────────────
    def _translate_local_var(self, decl):
        ctype = translate_type(decl.type.name)
        for declarator in decl.declarators:
            name = declarator.name
            if declarator.initializer:
                init = self._expr(declarator.initializer)
                self.emit(f'{ctype} {name} = {init};')
            else:
                self.emit(f'{ctype} {name};')

    # ── Control flow ──────────────────────────────────────────────────────────
    def _translate_if(self, stmt):
        cond = self._expr(stmt.condition)
        self.emit(f'if ({cond}) {{')
        self.indent_level += 1
        self._translate_block_or_stmt(stmt.then_statement)
        self.indent_level -= 1
        if stmt.else_statement:
            if isinstance(stmt.else_statement, javalang.tree.IfStatement):
                # else if
                cond2 = self._expr(stmt.else_statement.condition)
                self.emit(f'}} else if ({cond2}) {{')
                self.indent_level += 1
                self._translate_block_or_stmt(stmt.else_statement.then_statement)
                self.indent_level -= 1
                if stmt.else_statement.else_statement:
                    self.emit('} else {')
                    self.indent_level += 1
                    self._translate_block_or_stmt(stmt.else_statement.else_statement)
                    self.indent_level -= 1
                self.emit('}')
            else:
                self.emit('} else {')
                self.indent_level += 1
                self._translate_block_or_stmt(stmt.else_statement)
                self.indent_level -= 1
                self.emit('}')
        else:
            self.emit('}')

    def _translate_for(self, stmt):
        ctrl = stmt.control
        if isinstance(ctrl, javalang.tree.ForControl):
            init_str = ''
            if ctrl.init:
                # LocalVariableDeclaration or StatementExpression
                if isinstance(ctrl.init, javalang.tree.LocalVariableDeclaration):
                    ctype = translate_type(ctrl.init.type.name)
                    parts = []
                    for d in ctrl.init.declarators:
                        iv = self._expr(d.initializer) if d.initializer else '0'
                        parts.append(f'{ctype} {d.name} = {iv}')
                    init_str = ', '.join(parts)
                else:
                    init_str = self._expr(ctrl.init)

            cond_str = self._expr(ctrl.condition) if ctrl.condition else ''
            upd_str  = ', '.join(self._expr(u) for u in (ctrl.update or []))
            self.emit(f'for ({init_str}; {cond_str}; {upd_str}) {{')
        else:
            # Enhanced for (for-each) — approximate
            self.emit(f'/* for-each not directly translatable */')
            self.emit('for (;;) {')

        self.indent_level += 1
        self._translate_block_or_stmt(stmt.body)
        self.indent_level -= 1
        self.emit('}')

    def _translate_while(self, stmt):
        cond = self._expr(stmt.condition)
        self.emit(f'while ({cond}) {{')
        self.indent_level += 1
        self._translate_block_or_stmt(stmt.body)
        self.indent_level -= 1
        self.emit('}')

    def _translate_do_while(self, stmt):
        self.emit('do {')
        self.indent_level += 1
        self._translate_block_or_stmt(stmt.body)
        self.indent_level -= 1
        cond = self._expr(stmt.condition)
        self.emit(f'}} while ({cond});')

    def _translate_return(self, stmt):
        if stmt.expression:
            self.emit(f'return {self._expr(stmt.expression)};')
        else:
            self.emit('return;')

    def _translate_block_or_stmt(self, node):
        if isinstance(node, javalang.tree.BlockStatement):
            for s in node.statements:
                self._translate_stmt(s)
        elif isinstance(node, list):
            for s in node:
                self._translate_stmt(s)
        elif node:
            self._translate_stmt(node)

    # ── Statement expression ──────────────────────────────────────────────────
    def _translate_stmt_expr(self, expr):
        if isinstance(expr, javalang.tree.MethodInvocation):
            self._translate_method_call_stmt(expr)
        elif isinstance(expr, javalang.tree.Assignment):
            lhs = self._expr(expr.expressionl)
            rhs = self._expr(expr.value)
            self.emit(f'{lhs} {expr.type} {rhs};')
        else:
            self.emit(f'{self._expr(expr)};')

    def _translate_method_call_stmt(self, call):
        """Translate a method call used as a statement."""
        result = self._translate_method_call_expr(call)
        self.emit(f'{result};')

    def _translate_method_call_expr(self, call):
        """Return C string for a Java method call."""
        qualifier = call.qualifier   # e.g. 'System.out', 'Math', 'Integer'
        name      = call.member      # e.g. 'printf', 'sqrt', 'parseInt'
        args      = [self._expr(a) for a in (call.arguments or [])]

        # System.out.printf / println / print
        if qualifier in ('System.out', 'System.err'):
            if name == 'printf':
                fmt = args[0]
                rest = args[1:]
                # Java %n → C \n
                fmt_c = fmt.replace('%n', '\\n')
                if rest:
                    return f'printf({fmt_c}, {", ".join(rest)})'
                return f'printf({fmt_c})'
            elif name == 'println':
                if args:
                    return f'printf("%s\\n", {args[0]})'
                return 'printf("\\n")'
            elif name == 'print':
                if args:
                    return f'printf("%s", {args[0]})'
                return 'printf("")'

        # Math.*
        if qualifier == 'Math' and name in MATH_MAP:
            c_func = MATH_MAP[name]
            return f'{c_func}({", ".join(args)})'

        # Integer.parseInt, Double.parseDouble, Long.parseLong
        key = (qualifier, name)
        if key in PARSE_MAP:
            return f'{PARSE_MAP[key]}({", ".join(args)})'

        # Character.*
        if qualifier == 'Character' and name in CHAR_MAP:
            return f'{CHAR_MAP[name]}({", ".join(args)})'

        # String methods called on a variable: s.length(), s.compareTo(), etc.
        if qualifier and name == 'length':
            return f'strlen({qualifier})'
        if qualifier and name == 'compareTo':
            return f'strcmp({qualifier}, {", ".join(args)})'
        if qualifier and name == 'toUpperCase':
            return f'strupr({qualifier})'
        if qualifier and name == 'toLowerCase':
            return f'strlwr({qualifier})'
        if qualifier and name == 'contains':
            return f'strstr({qualifier}, {", ".join(args)}) != NULL'
        if qualifier and name == 'indexOf':
            return f'strchr({qualifier}, {", ".join(args)}) - {qualifier}'

        # Generic fallback
        if qualifier:
            return f'{qualifier}.{name}({", ".join(args)})'
        return f'{name}({", ".join(args)})'

    # ── Expression → C string ─────────────────────────────────────────────────
    def _expr(self, node):
        if node is None:
            return ''
        if isinstance(node, javalang.tree.Literal):
            val = node.value
            # Java boolean literals
            if val == 'true':  return '1'
            if val == 'false': return '0'
            # Java long literal: 100L → 100
            if val.endswith('L') or val.endswith('l'):
                return val[:-1]
            return val
        if isinstance(node, javalang.tree.MemberReference):
            # Build base: qualifier.member or just member
            base = f'{node.qualifier}.{node.member}' if node.qualifier else node.member
            # Apply prefix operators (++i, --i)
            for op in (node.prefix_operators or []):
                base = f'{op}{base}'
            # Apply selectors: ArraySelector → arr[i], MethodInvocation → chained call
            result = base
            for sel in (node.selectors or []):
                if isinstance(sel, javalang.tree.ArraySelector):
                    result = f'{result}[{self._expr(sel.index)}]'
                elif isinstance(sel, javalang.tree.MethodInvocation):
                    sel_args = [self._expr(a) for a in (sel.arguments or [])]
                    result = self._translate_method_call_expr_qualified(result, sel.member, sel_args)
            # Apply postfix operators (i++, i--)
            for op in (node.postfix_operators or []):
                result = f'{result}{op}'
            return result
        if isinstance(node, javalang.tree.BinaryOperation):
            left  = self._expr(node.operandl)
            right = self._expr(node.operandr)
            return f'({left} {node.operator} {right})'
        if isinstance(node, javalang.tree.MethodInvocation):
            return self._translate_method_call_expr(node)
        if isinstance(node, javalang.tree.Assignment):
            lhs = self._expr(node.expressionl)
            rhs = self._expr(node.value)
            return f'{lhs} {node.type} {rhs}'
        if isinstance(node, javalang.tree.ArrayCreator):
            ctype = translate_type(node.type.name)
            dim   = self._expr(node.dimensions[0]) if node.dimensions else '0'
            return f'/* new {ctype}[{dim}] - allocate manually in C */'
        if isinstance(node, javalang.tree.ArrayInitializer):
            vals = ', '.join(self._expr(v) for v in node.initializers)
            return f'{{{vals}}}'
        if isinstance(node, javalang.tree.TernaryExpression):
            cond    = self._expr(node.condition)
            iftrue  = self._expr(node.if_true)
            iffalse = self._expr(node.if_false)
            return f'({cond} ? {iftrue} : {iffalse})'
        if isinstance(node, javalang.tree.Cast):
            ctype = translate_type(node.type.name)
            expr  = self._expr(node.expression)
            return f'({ctype}){expr}'
        if isinstance(node, javalang.tree.ClassCreator):
            return f'/* new {node.type.name}(...) - use struct in C */'
        if isinstance(node, (list, tuple)):
            return ', '.join(self._expr(e) for e in node)
        return f'/* expr:{type(node).__name__} */'

    def _translate_method_call_expr_qualified(self, qualifier, name, args):
        """Helper for chained method calls on a computed qualifier string."""
        if name == 'length':      return f'strlen({qualifier})'
        if name == 'compareTo':   return f'strcmp({qualifier}, {args[0]})'
        if name == 'toUpperCase': return f'strupr({qualifier})'
        if name == 'toLowerCase': return f'strlwr({qualifier})'
        if name == 'contains':    return f'strstr({qualifier}, {args[0]}) != NULL'
        arg_str = ', '.join(args)
        return f'{qualifier}.{name}({arg_str})'



# ── Public API ────────────────────────────────────────────────────────────────
def translate_file(java_file_path):
    """Parse a Java file and return the C source as a string."""
    with open(java_file_path, 'r', encoding='utf-8') as f:
        source = f.read()
    return translate_string(source)


def translate_string(java_source):
    """Parse a Java source string and return the C source as a string."""
    translator = JavaToCTranslator()
    return translator.translate(java_source)
