# ─────────────────────────────────────────────────────────────────────────────
#  c_to_java.py
#  C → Java translator using pycparser (external AST library).
#
#  Key difference from the pure-Python version:
#    • pycparser does ALL the lexing and parsing for us.
#    • We only write the VISITOR — the code-generation step.
#    • We subclass pycparser.c_ast.NodeVisitor and override visit_* methods.
#
#  pycparser AST node types used:
#    FileAST       → top-level program
#    FuncDef       → function definition
#    Decl          → variable / parameter declaration
#    TypeDecl      → type wrapper inside Decl
#    IdentifierType→ the actual type name ('int', 'float', ...)
#    ArrayDecl     → array type
#    PtrDecl       → pointer type (treated as array/String)
#    ParamList     → function parameter list
#    Compound      → { ... } block
#    If            → if / else
#    For           → for loop
#    While         → while loop
#    Return        → return statement
#    FuncCall      → function call
#    Assignment    → assignment expression
#    BinaryOp      → binary expression
#    UnaryOp       → unary expression
#    Constant      → literal value
#    ID            → identifier
#    ArrayRef      → array[index]
#    NamedInitializer → struct / array initializer
# ─────────────────────────────────────────────────────────────────────────────

import pycparser
from pycparser import c_ast


# ── Type mapping ──────────────────────────────────────────────────────────────
TYPE_MAP = {
    'int':      'int',
    'float':    'float',
    'double':   'double',
    'char':     'char',
    'void':     'void',
    'long':     'long',
    'short':    'short',
    'unsigned': 'int',
    'bool':     'boolean',
}

# C printf → Java System.out.printf (same format, just different call)
PRINTF_FUNCS = {'printf', 'fprintf'}

# C string functions → Java equivalents (single-arg)
STRING_FUNC_1 = {
    'strlen':  lambda a: f'{a}.length()',
    'atoi':    lambda a: f'Integer.parseInt({a})',
    'atof':    lambda a: f'Double.parseDouble({a})',
    'atol':    lambda a: f'Long.parseLong({a})',
    'toupper': lambda a: f'Character.toUpperCase({a})',
    'tolower': lambda a: f'Character.toLowerCase({a})',
    'isalpha': lambda a: f'Character.isLetter({a})',
    'isdigit': lambda a: f'Character.isDigit({a})',
    'isspace': lambda a: f'Character.isWhitespace({a})',
    'isupper': lambda a: f'Character.isUpperCase({a})',
    'islower': lambda a: f'Character.isLowerCase({a})',
    'strupr':  lambda a: f'{a}.toUpperCase()',
    'strlwr':  lambda a: f'{a}.toLowerCase()',
    'sqrt':    lambda a: f'Math.sqrt({a})',
    'fabs':    lambda a: f'Math.abs({a})',
    'abs':     lambda a: f'Math.abs({a})',
    'ceil':    lambda a: f'Math.ceil({a})',
    'floor':   lambda a: f'Math.floor({a})',
    'round':   lambda a: f'Math.round({a})',
    'log':     lambda a: f'Math.log({a})',
    'log10':   lambda a: f'Math.log10({a})',
    'sin':     lambda a: f'Math.sin({a})',
    'cos':     lambda a: f'Math.cos({a})',
    'tan':     lambda a: f'Math.tan({a})',
    'rand':    lambda a: f'(int)(Math.random() * 32767)',
}

STRING_FUNC_2 = {
    'strcmp':  lambda a, b: f'{a}.compareTo({b})',
    'strcat':  lambda a, b: f'{a} + {b}',
    'strchr':  lambda a, b: f'{a}.indexOf({b}) >= 0',
    'strstr':  lambda a, b: f'{a}.contains({b})',
    'pow':     lambda a, b: f'Math.pow({a}, {b})',
}


def translate_type(c_type_str):
    """Map a C type string to its Java equivalent."""
    return TYPE_MAP.get(c_type_str, c_type_str)


# ── Visitor ───────────────────────────────────────────────────────────────────
class CToJavaVisitor(c_ast.NodeVisitor):
    """
    Walks a pycparser AST and emits Java source code.

    Unlike the pure-Python version where we wrote our own visit() dispatcher,
    here pycparser.c_ast.NodeVisitor already provides:
        • self.visit(node)          — dispatches to visit_ClassName(node)
        • self.generic_visit(node)  — visits all children (fallback)

    We just override the methods we care about.
    """

    def __init__(self):
        self.indent_level = 0
        self.output       = []   # list of lines
        self.needs_scanner = False
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

    def _expr(self, node):
        """Return the Java string for an expression node (non-emitting)."""
        return ExprVisitor().visit(node)

    # ── Top-level ─────────────────────────────────────────────────────────────
    def visit_FileAST(self, node):
        """
        FileAST is the root node pycparser gives us.
        Its .ext is a list of top-level declarations / function definitions.
        """
        # Check if scanf is used anywhere (need Scanner import)
        self.needs_scanner = _uses_scanf(node)

        if self.needs_scanner:
            self.emit('import java.util.Scanner;')
            self.emit_blank()

        self.emit('public class Main {')
        self.emit_blank()
        self.indent_level = 1

        for item in node.ext:
            if isinstance(item, c_ast.FuncDef):
                self.visit_FuncDef(item)
                self.emit_blank()
            elif isinstance(item, c_ast.Decl):
                # Global variable
                self._emit_global_decl(item)

        self.indent_level = 0
        self.emit('}')

    def _emit_global_decl(self, decl):
        """Emit a global variable as a Java static field."""
        jtype, name, is_arr, arr_size = _extract_decl(decl)
        if decl.init:
            init_str = self._expr(decl.init)
            self.emit(f'static {jtype} {name} = {init_str};')
        else:
            self.emit(f'static {jtype} {name};')

    # ── Function definition ───────────────────────────────────────────────────
    def visit_FuncDef(self, node):
        """
        FuncDef has:
          .decl       → Decl (contains name, type info)
          .param_decls→ old-style K&R params (usually None)
          .body       → Compound (the { } block)
        """
        func_name = node.decl.name
        self.is_main = (func_name == 'main')

        # Return type
        func_type = node.decl.type          # FuncDecl
        ret_type  = _get_type_str(func_type.type)
        java_ret  = 'void' if self.is_main else translate_type(ret_type)

        # Parameters
        params_str = ''
        if self.is_main:
            params_str = 'String[] args'
        elif func_type.args:
            params_str = self._params(func_type.args)

        sig = f'public static {java_ret} {func_name}({params_str}) {{'
        self.emit(sig)

        # Body
        self.indent_level += 1
        if self.is_main and self.needs_scanner:
            self.emit('Scanner sc = new Scanner(System.in);')

        self.visit_Compound(node.body)
        self.indent_level -= 1
        self.emit('}')

    def _params(self, param_list):
        """Convert a pycparser ParamList to a Java parameter string."""
        parts = []
        for param in param_list.params:
            jtype, name, is_arr, _ = _extract_decl(param)
            if is_arr:
                parts.append(f'{jtype}[] {name}')
            else:
                parts.append(f'{jtype} {name}')
        return ', '.join(parts)

    # ── Block / Compound ──────────────────────────────────────────────────────
    def visit_Compound(self, node):
        """
        Compound = { statements... }
        node.block_items is a list of statements / declarations.
        """
        if node.block_items:
            for stmt in node.block_items:
                self._visit_stmt(stmt)

    def _visit_stmt(self, node):
        """Dispatch a statement node to the right emitter."""
        if isinstance(node, c_ast.Decl):
            self._emit_local_decl(node)
        elif isinstance(node, c_ast.If):
            self.visit_If(node)
        elif isinstance(node, c_ast.For):
            self.visit_For(node)
        elif isinstance(node, c_ast.While):
            self.visit_While(node)
        elif isinstance(node, c_ast.DoWhile):
            self.visit_DoWhile(node)
        elif isinstance(node, c_ast.Return):
            self.visit_Return(node)
        elif isinstance(node, c_ast.FuncCall):
            self._emit_func_call_stmt(node)
        elif isinstance(node, c_ast.Assignment):
            self._emit_assignment(node)
        elif isinstance(node, c_ast.UnaryOp):
            # e.g. i++, ++i as statement
            self.emit(f'{self._expr(node)};')
        elif isinstance(node, c_ast.Break):
            self.emit('break;')
        elif isinstance(node, c_ast.Continue):
            self.emit('continue;')
        elif isinstance(node, c_ast.Compound):
            self.indent_level += 1
            self.visit_Compound(node)
            self.indent_level -= 1
        else:
            # Fallback: emit as expression statement
            self.emit(f'{self._expr(node)};')

    # ── Local variable declaration ────────────────────────────────────────────
    def _emit_local_decl(self, decl):
        """
        Decl inside a function body.
        pycparser gives us the type info nested inside decl.type.
        """
        jtype, name, is_arr, arr_size = _extract_decl(decl)

        if is_arr:
            if decl.init and isinstance(decl.init, c_ast.InitList):
                # int arr[] = {1,2,3}  →  int[] arr = {1,2,3};
                vals = ', '.join(self._expr(e) for e in decl.init.exprs)
                self.emit(f'{jtype}[] {name} = {{{vals}}};')
            elif arr_size:
                # int arr[5]  →  int[] arr = new int[5];
                self.emit(f'{jtype}[] {name} = new {jtype}[{arr_size}];')
            else:
                self.emit(f'{jtype}[] {name};')
        else:
            if decl.init:
                init_str = self._expr(decl.init)
                self.emit(f'{jtype} {name} = {init_str};')
            else:
                self.emit(f'{jtype} {name};')

    # ── Assignment ────────────────────────────────────────────────────────────
    def _emit_assignment(self, node):
        """Assignment: lvalue op= rvalue"""
        lhs = self._expr(node.lvalue)
        rhs = self._expr(node.rvalue)
        self.emit(f'{lhs} {node.op} {rhs};')

    # ── Function call as statement ────────────────────────────────────────────
    def _emit_func_call_stmt(self, node):
        """Translate a function call used as a statement."""
        name = node.name.name if isinstance(node.name, c_ast.ID) else self._expr(node.name)
        args = [self._expr(a) for a in (node.args.exprs if node.args else [])]

        # printf → System.out.printf
        if name in PRINTF_FUNCS:
            fmt = args[0]
            rest = args[1:]
            # Convert \n to %n for Java printf
            fmt_java = fmt.replace('\\n', '%n')
            if rest:
                self.emit(f'System.out.printf({fmt_java}, {", ".join(rest)});')
            else:
                # No format args — use println if just a string
                inner = fmt_java.strip('"').rstrip('%n')
                self.emit(f'System.out.printf({fmt_java});')
            return

        # scanf → sc.nextInt() etc.
        if name == 'scanf':
            fmt  = args[0].strip('"')
            vars_ = args[1:]
            for i, var in enumerate(vars_):
                # strip & prefix
                var_name = var.lstrip('&')
                if '%d' in fmt or '%i' in fmt:
                    self.emit(f'{var_name} = sc.nextInt();')
                elif '%f' in fmt or '%lf' in fmt:
                    self.emit(f'{var_name} = sc.nextDouble();')
                elif '%s' in fmt:
                    self.emit(f'{var_name} = sc.next();')
                elif '%c' in fmt:
                    self.emit(f'{var_name} = sc.next().charAt(0);')
                else:
                    self.emit(f'{var_name} = sc.nextLine();')
            return

        # String / math library functions as statements (e.g. strcpy)
        translated = _translate_lib_func(name, args)
        if translated:
            self.emit(f'{translated};')
            return

        # Regular function call
        self.emit(f'{name}({", ".join(args)});')

    # ── Control flow ──────────────────────────────────────────────────────────
    def visit_If(self, node):
        cond = self._expr(node.cond)
        self.emit(f'if ({cond}) {{')
        self.indent_level += 1
        self._visit_stmt(node.iftrue)
        self.indent_level -= 1
        if node.iffalse:
            if isinstance(node.iffalse, c_ast.If):
                # else if
                self.emit('} else ')
                # Temporarily remove the newline by popping and re-emitting
                last = self.output.pop()
                self.output.append(last)
                self.emit('} else {')
                self.output.pop()
                # Emit else-if inline
                cond2 = self._expr(node.iffalse.cond)
                prev = self.output.pop()
                self.output.append(prev.rstrip('{').rstrip() + f' else if ({cond2}) {{')
                self.indent_level += 1
                self._visit_stmt(node.iffalse.iftrue)
                self.indent_level -= 1
                if node.iffalse.iffalse:
                    self.emit('} else {')
                    self.indent_level += 1
                    self._visit_stmt(node.iffalse.iffalse)
                    self.indent_level -= 1
                self.emit('}')
            else:
                self.emit('} else {')
                self.indent_level += 1
                self._visit_stmt(node.iffalse)
                self.indent_level -= 1
                self.emit('}')
        else:
            self.emit('}')

    def visit_For(self, node):
        """
        For node has: .init (DeclList or Assignment), .cond, .next, .stmt
        """
        init_str = ''
        if node.init:
            if isinstance(node.init, c_ast.DeclList):
                # for (int i = 0; ...)
                parts = []
                for d in node.init.decls:
                    jtype, name, _, _ = _extract_decl(d)
                    init_val = self._expr(d.init) if d.init else '0'
                    parts.append(f'{jtype} {name} = {init_val}')
                init_str = ', '.join(parts)
            else:
                init_str = self._expr(node.init).rstrip(';')

        cond_str = self._expr(node.cond) if node.cond else ''
        next_str = self._expr(node.next) if node.next else ''

        self.emit(f'for ({init_str}; {cond_str}; {next_str}) {{')
        self.indent_level += 1
        if isinstance(node.stmt, c_ast.Compound):
            self.visit_Compound(node.stmt)
        else:
            self._visit_stmt(node.stmt)
        self.indent_level -= 1
        self.emit('}')

    def visit_While(self, node):
        cond = self._expr(node.cond)
        self.emit(f'while ({cond}) {{')
        self.indent_level += 1
        if isinstance(node.stmt, c_ast.Compound):
            self.visit_Compound(node.stmt)
        else:
            self._visit_stmt(node.stmt)
        self.indent_level -= 1
        self.emit('}')

    def visit_DoWhile(self, node):
        self.emit('do {')
        self.indent_level += 1
        if isinstance(node.stmt, c_ast.Compound):
            self.visit_Compound(node.stmt)
        else:
            self._visit_stmt(node.stmt)
        self.indent_level -= 1
        cond = self._expr(node.cond)
        self.emit(f'}} while ({cond});')

    def visit_Return(self, node):
        if node.expr:
            val = self._expr(node.expr)
            # In main(), return 0 → just 'return;'
            if self.is_main and val == '0':
                self.emit('return;')
            else:
                self.emit(f'return {val};')
        else:
            self.emit('return;')


# ── Expression visitor (returns string, does NOT emit) ────────────────────────
class ExprVisitor(c_ast.NodeVisitor):
    """
    A second visitor that converts expression nodes to Java strings.
    This is separate from CToJavaVisitor so we can call it recursively
    without side effects on the output buffer.
    """

    def visit_Constant(self, node):
        val = node.value
        # Float literals: add 'f' suffix if not already present
        if node.type in ('float',):
            if not val.endswith('f') and not val.endswith('F'):
                val += 'f'
        return val

    def visit_ID(self, node):
        return node.name

    def visit_BinaryOp(self, node):
        left  = self.visit(node.left)
        right = self.visit(node.right)
        return f'({left} {node.op} {right})'

    def visit_UnaryOp(self, node):
        expr = self.visit(node.expr)
        op   = node.op
        if op == 'p++': return f'{expr}++'
        if op == 'p--': return f'{expr}--'
        if op == '++':  return f'++{expr}'
        if op == '--':  return f'--{expr}'
        if op == '&':   return expr   # address-of: just use variable name
        if op == '*':   return expr   # dereference: just use variable name
        return f'{op}{expr}'

    def visit_Assignment(self, node):
        lhs = self.visit(node.lvalue)
        rhs = self.visit(node.rvalue)
        return f'{lhs} {node.op} {rhs}'

    def visit_FuncCall(self, node):
        name = node.name.name if isinstance(node.name, c_ast.ID) else self.visit(node.name)
        args = [self.visit(a) for a in (node.args.exprs if node.args else [])]

        # printf → System.out.printf
        if name in PRINTF_FUNCS:
            fmt = args[0]
            rest = args[1:]
            fmt_java = fmt.replace('\\n', '%n')
            if rest:
                return f'System.out.printf({fmt_java}, {", ".join(rest)})'
            return f'System.out.printf({fmt_java})'

        # Library function translation
        translated = _translate_lib_func(name, args)
        if translated:
            return translated

        return f'{name}({", ".join(args)})'

    def visit_ArrayRef(self, node):
        arr   = self.visit(node.name)
        index = self.visit(node.subscript)
        return f'{arr}[{index}]'

    def visit_StructRef(self, node):
        obj    = self.visit(node.name)
        member = node.field.name
        return f'{obj}.{member}'

    def visit_Cast(self, node):
        type_str = _get_type_str(node.to_type.type)
        java_type = translate_type(type_str)
        expr = self.visit(node.expr)
        return f'({java_type}){expr}'

    def visit_TernaryOp(self, node):
        cond  = self.visit(node.cond)
        iftrue  = self.visit(node.iftrue)
        iffalse = self.visit(node.iffalse)
        return f'({cond} ? {iftrue} : {iffalse})'

    def visit_InitList(self, node):
        vals = ', '.join(self.visit(e) for e in node.exprs)
        return f'{{{vals}}}'

    def visit_ExprList(self, node):
        return ', '.join(self.visit(e) for e in node.exprs)

    def generic_visit(self, node):
        return f'/* unsupported: {type(node).__name__} */'


# ── Helper functions ──────────────────────────────────────────────────────────
def _extract_decl(decl):
    """
    Extract (java_type, name, is_array, array_size) from a pycparser Decl.
    pycparser nests type info:
      Decl → TypeDecl → IdentifierType   (simple variable)
      Decl → ArrayDecl → TypeDecl → ...  (array)
      Decl → PtrDecl  → TypeDecl → ...   (pointer)
    """
    name    = decl.name
    dtype   = decl.type
    is_arr  = False
    arr_size = None

    if isinstance(dtype, c_ast.ArrayDecl):
        is_arr = True
        if dtype.dim:
            arr_size = ExprVisitor().visit(dtype.dim)
        dtype = dtype.type   # unwrap to TypeDecl

    elif isinstance(dtype, c_ast.PtrDecl):
        # Treat char* as String, others as array
        inner = dtype.type
        type_str = _get_type_str(inner)
        if type_str == 'char':
            return ('String', name, False, None)
        is_arr = True
        dtype = inner

    type_str = _get_type_str(dtype)
    jtype    = translate_type(type_str)
    return (jtype, name, is_arr, arr_size)


def _get_type_str(type_node):
    """Recursively unwrap pycparser type nodes to get the base type string."""
    if isinstance(type_node, c_ast.TypeDecl):
        return _get_type_str(type_node.type)
    if isinstance(type_node, c_ast.IdentifierType):
        return ' '.join(type_node.names)
    if isinstance(type_node, c_ast.PtrDecl):
        return _get_type_str(type_node.type)
    if isinstance(type_node, c_ast.ArrayDecl):
        return _get_type_str(type_node.type)
    if isinstance(type_node, c_ast.FuncDecl):
        return _get_type_str(type_node.type)
    return 'void'


def _translate_lib_func(name, args):
    """Return Java equivalent string for a C library function, or None."""
    if name in STRING_FUNC_1 and len(args) >= 1:
        return STRING_FUNC_1[name](args[0])
    if name in STRING_FUNC_2 and len(args) >= 2:
        return STRING_FUNC_2[name](args[0], args[1])
    return None


def _uses_scanf(node):
    """Walk the entire AST to check if scanf is called anywhere."""
    class ScanfFinder(c_ast.NodeVisitor):
        def __init__(self):
            self.found = False
        def visit_FuncCall(self, node):
            if isinstance(node.name, c_ast.ID) and node.name.name == 'scanf':
                self.found = True
            self.generic_visit(node)
    finder = ScanfFinder()
    finder.visit(node)
    return finder.found


# ── Public API ────────────────────────────────────────────────────────────────
def translate_file(c_file_path):
    """
    Parse a C file with pycparser and return the Java source as a string.

    pycparser requires a real C preprocessor for #include directives.
    We use pycparser's bundled 'fake_libc_include' headers so that
    standard headers like <stdio.h> are resolved without needing GCC.
    """
    import os
    # pycparser ships fake headers for exactly this purpose
    fake_libc = os.path.join(
        os.path.dirname(pycparser.__file__),
        'utils', 'fake_libc_include'
    )
    ast = pycparser.parse_file(
        c_file_path,
        use_cpp=True,
        cpp_path='gcc',          # needs gcc on PATH (or cpp)
        cpp_args=['-E', f'-I{fake_libc}']
    )
    visitor = CToJavaVisitor()
    visitor.visit(ast)
    return visitor.result()


def translate_string(c_source):
    """
    Parse a C source string directly (no preprocessor needed).
    Useful for testing without #include directives.
    """
    parser = pycparser.CParser()
    ast    = parser.parse(c_source, filename='<string>')
    visitor = CToJavaVisitor()
    visitor.visit(ast)
    return visitor.result()
