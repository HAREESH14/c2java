# =============================================================================
#  c_to_java.py  -- C -> Java translator
#
#  Uses: pycparser (C AST)  ->  Java source strings
#  Adapted from lib_translator/c_to_java.py with enhancements:
#    + Switch/case support
#    + Error recovery (unknown nodes emit /* unsupported */ comment)
#    + Scanner/stdin support (scanf -> sc.nextInt etc.)
#    + Math.*, Character.*, Integer.parseInt etc.
# =============================================================================

import pycparser
from pycparser import c_ast

TYPE_MAP = {
    'int':'int','float':'float','double':'double','char':'char',
    'void':'void','long':'long','short':'short','unsigned':'int','bool':'boolean',
}

PRINTF_FUNCS = {'printf','fprintf'}

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
    'sqrt':    lambda a: f'Math.sqrt({a})',
    'abs':     lambda a: f'Math.abs({a})',
    'fabs':    lambda a: f'Math.abs({a})',
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
    'strcmp':  lambda a,b: f'{a}.compareTo({b})',
    'strcat':  lambda a,b: f'{a} + {b}',
    'strchr':  lambda a,b: f'{a}.indexOf({b}) >= 0',
    'strstr':  lambda a,b: f'{a}.contains({b})',
    'pow':     lambda a,b: f'Math.pow({a}, {b})',
    'strcpy':  lambda a,b: f'{b}',   # simplified
}
PARSE_MAP = {
    ('Integer','parseInt'):   'Integer.parseInt',
    ('Double','parseDouble'): 'Double.parseDouble',
    ('Long','parseLong'):     'Long.parseLong',
}

def _jtype(ct): return TYPE_MAP.get(ct, ct)
def _lib(name, args):
    if name in STRING_FUNC_1 and args: return STRING_FUNC_1[name](args[0])
    if name in STRING_FUNC_2 and len(args)>=2: return STRING_FUNC_2[name](args[0],args[1])
    return None


# ---------------------------------------------------------------------------
class ExprVisitor(c_ast.NodeVisitor):

    def visit_Constant(self, n):
        v = n.value
        if n.type == 'float' and not v.endswith(('f','F')): v += 'f'
        return v

    def visit_ID(self, n): return n.name

    def visit_BinaryOp(self, n):
        return f'({self.visit(n.left)} {n.op} {self.visit(n.right)})'

    def visit_UnaryOp(self, n):
        e, op = self.visit(n.expr), n.op
        if op=='p++': return f'{e}++'
        if op=='p--': return f'{e}--'
        if op in ('&','*'): return e       # address-of / deref -> strip
        return f'{op}{e}'

    def visit_Assignment(self, n):
        return f'{self.visit(n.lvalue)} {n.op} {self.visit(n.rvalue)}'

    def visit_FuncCall(self, n):
        name = n.name.name if isinstance(n.name,c_ast.ID) else self.visit(n.name)
        args = [self.visit(a) for a in (n.args.exprs if n.args else [])]
        if name in PRINTF_FUNCS:
            rest = args[1:]
            fmt  = args[0].replace('\\n','%n') if args else '""'
            return (f'System.out.printf({fmt}, {", ".join(rest)})' if rest
                    else f'System.out.printf({fmt})')
        t = _lib(name, args)
        if t: return t
        return f'{name}({", ".join(args)})'

    def visit_ArrayRef(self, n):
        return f'{self.visit(n.name)}[{self.visit(n.subscript)}]'

    def visit_StructRef(self, n):
        return f'{self.visit(n.name)}.{n.field.name}'

    def visit_Cast(self, n):
        return f'({_jtype(_gtype(n.to_type.type))}){self.visit(n.expr)}'

    def visit_TernaryOp(self, n):
        return f'({self.visit(n.cond)} ? {self.visit(n.iftrue)} : {self.visit(n.iffalse)})'

    def visit_InitList(self, n):
        return '{' + ', '.join(self.visit(e) for e in n.exprs) + '}'

    def visit_ExprList(self, n):
        return ', '.join(self.visit(e) for e in n.exprs)

    def generic_visit(self, n):
        return f'/* expr:{type(n).__name__} */'


def _gtype(t):
    if isinstance(t, c_ast.TypeDecl):    return _gtype(t.type)
    if isinstance(t, c_ast.IdentifierType): return ' '.join(t.names)
    if isinstance(t, (c_ast.PtrDecl, c_ast.ArrayDecl, c_ast.FuncDecl)):
        return _gtype(t.type)
    return 'void'

def _extract(decl):
    name   = decl.name
    dtype  = decl.type
    is_arr = False
    arr_sz = None
    if isinstance(dtype, c_ast.ArrayDecl):
        is_arr = True
        arr_sz = ExprVisitor().visit(dtype.dim) if dtype.dim else None
        dtype  = dtype.type
    elif isinstance(dtype, c_ast.PtrDecl):
        inner  = dtype.type
        ts     = _gtype(inner)
        if ts == 'char': return ('String', name, False, None)
        is_arr = True
        dtype  = inner
    ts    = _gtype(dtype)
    return (_jtype(ts), name, is_arr, arr_sz)

def _uses_scanf(node):
    class F(c_ast.NodeVisitor):
        found = False
        def visit_FuncCall(self, n):
            if isinstance(n.name,c_ast.ID) and n.name.name=='scanf': self.found=True
            self.generic_visit(n)
    f=F(); f.visit(node); return f.found


# ---------------------------------------------------------------------------
class CToJavaVisitor(c_ast.NodeVisitor):

    def __init__(self):
        self.indent  = 0
        self.output  = []
        self.scanner = False
        self.is_main = False

    def ind(self): return '    '*self.indent
    def emit(self, s): self.output.append(self.ind()+s)
    def blank(self): self.output.append('')
    def result(self): return '\n'.join(self.output)
    def _e(self, n): return ExprVisitor().visit(n)

    # ── Top-level ─────────────────────────────────────────────────────────────
    def visit_FileAST(self, node):
        self.scanner = _uses_scanf(node)
        needs_math  = any(f in str(node) for f in ('sqrt','pow','sin','cos','Math'))
        needs_str   = any(f in str(node) for f in ('strlen','strcmp','strcpy'))

        if self.scanner:   self.emit('import java.util.Scanner;'); self.blank()
        if needs_math:     self.emit('import java.lang.Math;');    self.blank()
        self.emit('public class Main {'); self.blank()
        self.indent = 1
        for item in node.ext:
            if isinstance(item, c_ast.FuncDef):
                self.visit_FuncDef(item); self.blank()
            elif isinstance(item, c_ast.Decl):
                jt_, name, is_arr, sz = _extract(item)
                if item.init: self.emit(f'static {jt_} {name} = {self._e(item.init)};')
                else:         self.emit(f'static {jt_} {name};')
        self.indent = 0
        self.emit('}')

    # ── Function def ──────────────────────────────────────────────────────────
    def visit_FuncDef(self, node):
        fname    = node.decl.name
        self.is_main = (fname == 'main')
        ftype    = node.decl.type
        ret      = _jtype(_gtype(ftype.type))
        java_ret = 'void' if self.is_main else ret
        params   = 'String[] args' if self.is_main else (
            self._params(ftype.args) if ftype.args else '')
        self.emit(f'public static {java_ret} {fname}({params}) {{')
        self.indent += 1
        if self.is_main and self.scanner:
            self.emit('Scanner sc = new Scanner(System.in);')
        self.visit_Compound(node.body)
        self.indent -= 1
        self.emit('}')

    def _params(self, pl):
        parts = []
        for p in pl.params:
            jt_, nm, is_arr, _ = _extract(p)
            parts.append(f'{jt_}[] {nm}' if is_arr else f'{jt_} {nm}')
        return ', '.join(parts)

    # ── Compound ──────────────────────────────────────────────────────────────
    def visit_Compound(self, n):
        if n.block_items:
            for s in n.block_items: self._stmt(s)

    def _stmt(self, n):
        if isinstance(n, c_ast.Decl):       self._local(n)
        elif isinstance(n, c_ast.If):       self._if(n)
        elif isinstance(n, c_ast.For):      self._for(n)
        elif isinstance(n, c_ast.While):    self._while(n)
        elif isinstance(n, c_ast.DoWhile):  self._dowhile(n)
        elif isinstance(n, c_ast.Return):   self._return(n)
        elif isinstance(n, c_ast.FuncCall): self._call_stmt(n)
        elif isinstance(n, c_ast.Assignment): self.emit(f'{self._e(n.lvalue)} {n.op} {self._e(n.rvalue)};')
        elif isinstance(n, c_ast.UnaryOp):  self.emit(f'{self._e(n)};')
        elif isinstance(n, c_ast.Break):    self.emit('break;')
        elif isinstance(n, c_ast.Continue): self.emit('continue;')
        elif isinstance(n, c_ast.Switch):   self._switch(n)
        elif isinstance(n, c_ast.Compound):
            self.indent+=1; self.visit_Compound(n); self.indent-=1
        else:
            self.emit(f'/* unsupported: {type(n).__name__} */')

    def _local(self, d):
        jt_, nm, is_arr, sz = _extract(d)
        if is_arr:
            if d.init and isinstance(d.init, c_ast.InitList):
                vals = ', '.join(self._e(e) for e in d.init.exprs)
                self.emit(f'{jt_}[] {nm} = {{{vals}}};')
            elif sz:
                self.emit(f'{jt_}[] {nm} = new {jt_}[{sz}];')
            else:
                self.emit(f'{jt_}[] {nm};')
        else:
            if d.init: self.emit(f'{jt_} {nm} = {self._e(d.init)};')
            else:      self.emit(f'{jt_} {nm};')

    def _if(self, n):
        self.emit(f'if ({self._e(n.cond)}) {{')
        self.indent+=1; self._stmt(n.iftrue); self.indent-=1
        if n.iffalse:
            if isinstance(n.iffalse, c_ast.If):
                cond2 = self._e(n.iffalse.cond)
                # rewrite last line to "} else if ..."
                self.output[-1] if self.output else None
                prev = self.output.pop() if self.output and self.output[-1].strip()=='}' else None
                if prev: self.output.append(self.ind() + f'}} else if ({cond2}) {{')
                else:    self.emit(f'}} else if ({cond2}) {{')
                self.indent+=1; self._stmt(n.iffalse.iftrue); self.indent-=1
                if n.iffalse.iffalse:
                    self.emit('} else {')
                    self.indent+=1; self._stmt(n.iffalse.iffalse); self.indent-=1
                self.emit('}')
            else:
                self.emit('} else {')
                self.indent+=1; self._stmt(n.iffalse); self.indent-=1
                self.emit('}')
        else:
            self.emit('}')

    def _for(self, n):
        init_s = ''
        if n.init:
            if isinstance(n.init, c_ast.DeclList):
                parts = []
                for d in n.init.decls:
                    jt_, nm, _, _ = _extract(d)
                    iv = self._e(d.init) if d.init else '0'
                    parts.append(f'{jt_} {nm} = {iv}')
                init_s = ', '.join(parts)
            else:
                init_s = self._e(n.init).rstrip(';')
        cond_s = self._e(n.cond) if n.cond else ''
        next_s = self._e(n.next) if n.next else ''
        self.emit(f'for ({init_s}; {cond_s}; {next_s}) {{')
        self.indent+=1
        if isinstance(n.stmt, c_ast.Compound): self.visit_Compound(n.stmt)
        else: self._stmt(n.stmt)
        self.indent-=1; self.emit('}')

    def _while(self, n):
        self.emit(f'while ({self._e(n.cond)}) {{')
        self.indent+=1
        if isinstance(n.stmt, c_ast.Compound): self.visit_Compound(n.stmt)
        else: self._stmt(n.stmt)
        self.indent-=1; self.emit('}')

    def _dowhile(self, n):
        self.emit('do {')
        self.indent+=1
        if isinstance(n.stmt, c_ast.Compound): self.visit_Compound(n.stmt)
        else: self._stmt(n.stmt)
        self.indent-=1; self.emit(f'}} while ({self._e(n.cond)});')

    def _return(self, n):
        if n.expr:
            v = self._e(n.expr)
            self.emit('return;' if (self.is_main and v=='0') else f'return {v};')
        else:
            self.emit('return;')

    def _switch(self, n):
        self.emit(f'switch ({self._e(n.cond)}) {{')
        self.indent+=1
        if isinstance(n.stmt, c_ast.Compound) and n.stmt.block_items:
            for item in n.stmt.block_items:
                if isinstance(item, c_ast.Case):
                    self.emit(f'case {self._e(item.expr)}:')
                    self.indent+=1
                    for s in (item.stmts or []): self._stmt(s)
                    self.indent-=1
                elif isinstance(item, c_ast.Default):
                    self.emit('default:')
                    self.indent+=1
                    for s in (item.stmts or []): self._stmt(s)
                    self.indent-=1
        self.indent-=1; self.emit('}')

    def _call_stmt(self, n):
        name = n.name.name if isinstance(n.name,c_ast.ID) else self._e(n.name)
        args = [self._e(a) for a in (n.args.exprs if n.args else [])]

        if name in PRINTF_FUNCS:
            fmt  = args[0].replace('\\n','%n') if args else '""'
            rest = args[1:]
            if rest: self.emit(f'System.out.printf({fmt}, {", ".join(rest)});')
            else:    self.emit(f'System.out.printf({fmt});')
            return
        if name == 'scanf':
            fmt   = args[0].strip('"') if args else ''
            vars_ = args[1:]
            specs = []
            i = 0
            while i < len(fmt):
                if fmt[i]=='%' and i+1<len(fmt):
                    specs.append(fmt[i:i+2]); i+=2
                else: i+=1
            for idx, var in enumerate(vars_):
                vn  = var.lstrip('&')
                sp  = specs[idx] if idx<len(specs) else '%d'
                if sp in ('%d','%i'):  self.emit(f'{vn} = sc.nextInt();')
                elif sp == '%f':              self.emit(f'{vn} = sc.nextFloat();')
                elif sp in ('%lf','%g'):      self.emit(f'{vn} = sc.nextDouble();')
                elif sp == '%s':       self.emit(f'{vn} = sc.next();')
                elif sp == '%c':       self.emit(f'{vn} = sc.next().charAt(0);')
                else:                  self.emit(f'{vn} = sc.nextLine();')
            return

        t = _lib(name, args)
        if t: self.emit(f'{t};'); return
        self.emit(f'{name}({", ".join(args)});')


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------
def translate_string(c_source: str) -> str:
    parser  = pycparser.CParser()
    try:
        ast = parser.parse(c_source, filename='<string>')
    except pycparser.plyparser.ParseError as e:
        raise ValueError(f'C parse error: {e}') from e
    v = CToJavaVisitor()
    v.visit(ast)
    return v.result()


def translate_file(c_path: str) -> str:
    """Parse a C file. Tries pycparser fake_libc first, strips includes on failure."""
    import re, os
    # Try with fake libc headers first
    fake = os.path.join(os.path.dirname(pycparser.__file__), 'utils', 'fake_libc_include')
    try:
        ast = pycparser.parse_file(c_path, use_cpp=True,
                                   cpp_path='gcc', cpp_args=['-E', f'-I{fake}'])
        v = CToJavaVisitor(); v.visit(ast); return v.result()
    except Exception:
        pass
    # Fallback: strip includes and comments, parse string
    with open(c_path, encoding='utf-8') as f: src = f.read()
    src = re.sub(r'//.*?$|/\*.*?\*/', '', src, flags=re.M|re.S)
    src = '\n'.join(l for l in src.splitlines() if not l.strip().startswith('#'))
    return translate_string(src)
