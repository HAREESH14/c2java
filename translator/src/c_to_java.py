# =============================================================================
#  c_to_java.py  -- C -> Java translator (enhanced)
#
#  Uses: pycparser (C AST)  ->  Java source strings
#
#  Supported features:
#    All types + char[]/char* -> String, arrays (1D/2D), if/else, for, while,
#    do-while, break, continue, switch/case, functions -> static methods,
#    compound assign, prefix/postfix ++/--, ternary, cast,
#    printf -> System.out.printf, scanf -> Scanner,
#    strlen/strcmp/strcpy/strcat/strchr/strstr -> String methods,
#    Math.* (sqrt/pow/sin/cos/tan/etc), Character.* (toupper/tolower/isXxx),
#    atoi/atof/atol -> Integer.parseInt/Double.parseDouble/Long.parseLong,
#    puts -> println, exit -> System.exit, sizeof -> constant or .length,
#    NULL -> null, const -> final, struct -> class, enum -> enum,
#    malloc/free -> new/comment, #define constants, unsigned types
# =============================================================================

import pycparser
from pycparser import c_ast

TYPE_MAP = {
    'int':'int','float':'float','double':'double','char':'char',
    'void':'void','long':'long','short':'short','unsigned':'int',
    'bool':'boolean','_Bool':'boolean',
    'unsigned int':'int','unsigned char':'int','unsigned long':'long',
    'unsigned short':'short','signed':'int','size_t':'int',
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
    'isalnum': lambda a: f'Character.isLetterOrDigit({a})',
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
    'asin':    lambda a: f'Math.asin({a})',
    'acos':    lambda a: f'Math.acos({a})',
    'atan':    lambda a: f'Math.atan({a})',
    'exp':     lambda a: f'Math.exp({a})',
    'rand':    lambda a: f'(int)(Math.random() * 32767)',
    'puts':    lambda a: f'System.out.println({a})',
    'free':    lambda a: f'/* free({a}) -- Java has GC */',
    'getchar': lambda a: f'(char)System.in.read()',
}
STRING_FUNC_2 = {
    'strcmp':   lambda a,b: f'{a}.compareTo({b})',
    'strncmp': lambda a,b: f'{a}.substring(0,{b}).compareTo',
    'strcat':  lambda a,b: f'{a} + {b}',
    'strchr':  lambda a,b: f'{a}.indexOf({b}) >= 0',
    'strstr':  lambda a,b: f'{a}.contains({b})',
    'pow':     lambda a,b: f'Math.pow({a}, {b})',
    'fmax':    lambda a,b: f'Math.max({a}, {b})',
    'fmin':    lambda a,b: f'Math.min({a}, {b})',
    'strcpy':  lambda a,b: f'{b}',   # simplified
    'strncpy': lambda a,b: f'{b}',   # simplified
    'atan2':   lambda a,b: f'Math.atan2({a}, {b})',
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
        # Replace NULL/0 in pointer context
        if v == 'NULL' or (n.type == 'int' and v == '0'):
            pass  # keep as is, context-dependent
        return v

    def visit_ID(self, n):
        if n.name == 'NULL': return 'null'
        if n.name == 'M_PI': return 'Math.PI'
        if n.name == 'M_E': return 'Math.E'
        if n.name == 'INT_MAX': return 'Integer.MAX_VALUE'
        if n.name == 'INT_MIN': return 'Integer.MIN_VALUE'
        if n.name == 'RAND_MAX': return '32767'
        if n.name == 'EOF': return '-1'
        if n.name == 'true' or n.name == 'false': return n.name
        return n.name

    def visit_BinaryOp(self, n):
        return f'({self.visit(n.left)} {n.op} {self.visit(n.right)})'

    def visit_UnaryOp(self, n):
        e, op = self.visit(n.expr), n.op
        if op=='p++': return f'{e}++'
        if op=='p--': return f'{e}--'
        if op in ('&','*'): return e       # address-of / deref -> strip
        if op == 'sizeof':
            return f'/* sizeof({e}) */ 4'
        return f'{op}{e}'

    def visit_Assignment(self, n):
        return f'{self.visit(n.lvalue)} {n.op} {self.visit(n.rvalue)}'

    def visit_FuncCall(self, n):
        name = n.name.name if isinstance(n.name,c_ast.ID) else self.visit(n.name)
        args = [self.visit(a) for a in (n.args.exprs if n.args else [])]

        # Handle sizeof specially
        if name == 'sizeof':
            if args:
                return f'/* sizeof */ 4'
            return '4'

        # Handle putchar
        if name == 'putchar':
            return f'System.out.print((char){args[0]})'

        # Handle exit
        if name == 'exit':
            return f'System.exit({args[0] if args else "0"})'

        # Handle malloc
        if name == 'malloc' or name == 'calloc':
            return f'new int[{args[0] if args else "10"}]'

        # Handle sprintf/snprintf
        if name in ('sprintf','snprintf'):
            if len(args) >= 2:
                return f'String.format({", ".join(args[1:])})'
            return f'String.format({", ".join(args)})'

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

    def visit_Compound(self, n):
        return '/* compound */'

    def visit_Typename(self, n):
        return _jtype(_gtype(n.type))

    def generic_visit(self, n):
        return f'/* expr:{type(n).__name__} */'


def _gtype(t):
    if isinstance(t, c_ast.TypeDecl):    return _gtype(t.type)
    if isinstance(t, c_ast.IdentifierType): return ' '.join(t.names)
    if isinstance(t, (c_ast.PtrDecl, c_ast.ArrayDecl, c_ast.FuncDecl)):
        return _gtype(t.type)
    return 'void'

def _is_const(decl):
    """Check if a declaration has const qualifier."""
    if hasattr(decl, 'quals') and decl.quals and 'const' in decl.quals:
        return True
    if hasattr(decl, 'type'):
        t = decl.type
        if hasattr(t, 'quals') and t.quals and 'const' in t.quals:
            return True
        if isinstance(t, c_ast.TypeDecl) and hasattr(t, 'quals') and t.quals and 'const' in t.quals:
            return True
    return False

def _extract(decl):
    name   = decl.name
    dtype  = decl.type
    is_arr = False
    arr_sz = None
    is_2d  = False
    arr_sz2 = None
    if isinstance(dtype, c_ast.ArrayDecl):
        # Check for 2D array: ArrayDecl(ArrayDecl(...))
        if isinstance(dtype.type, c_ast.ArrayDecl):
            is_2d = True
            arr_sz  = ExprVisitor().visit(dtype.dim) if dtype.dim else None
            arr_sz2 = ExprVisitor().visit(dtype.type.dim) if dtype.type.dim else None
            inner_type = _gtype(dtype.type.type)
            if inner_type == 'char':
                return ('String', name, True, arr_sz, False, None)
            return (_jtype(inner_type), name, True, arr_sz, True, arr_sz2)
        # char[] -> String in Java (same as char*)
        inner_type = _gtype(dtype.type)
        if inner_type == 'char':
            return ('String', name, False, None, False, None)
        is_arr = True
        arr_sz = ExprVisitor().visit(dtype.dim) if dtype.dim else None
        dtype  = dtype.type
    elif isinstance(dtype, c_ast.PtrDecl):
        inner  = dtype.type
        ts     = _gtype(inner)
        if ts == 'char': return ('String', name, False, None, False, None)
        is_arr = True
        dtype  = inner
    ts    = _gtype(dtype)
    return (_jtype(ts), name, is_arr, arr_sz, is_2d, arr_sz2)

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
        needs_math  = any(f in str(node) for f in ('sqrt','pow','sin','cos','Math','fabs','ceil','floor','log','exp'))

        if self.scanner:   self.emit('import java.util.Scanner;'); self.blank()
        if needs_math:     self.emit('import java.lang.Math;');    self.blank()
        self.emit('public class Main {'); self.blank()
        self.indent = 1

        for item in node.ext:
            if isinstance(item, c_ast.FuncDef):
                self.visit_FuncDef(item); self.blank()
            elif isinstance(item, c_ast.Decl):
                if isinstance(item.type, c_ast.Enum):
                    self._enum_decl(item)
                elif isinstance(item.type, c_ast.Struct):
                    self._struct_decl(item)
                elif isinstance(item.type, c_ast.FuncDecl):
                    pass  # skip forward declarations
                else:
                    jt_, name, is_arr, sz, is_2d, sz2 = _extract(item)
                    is_const = _is_const(item)
                    prefix = 'static final' if is_const else 'static'
                    if is_2d:
                        if item.init:
                            self.emit(f'{prefix} {jt_}[][] {name} = {self._e(item.init)};')
                        elif sz and sz2:
                            self.emit(f'{prefix} {jt_}[][] {name} = new {jt_}[{sz}][{sz2}];')
                        else:
                            self.emit(f'{prefix} {jt_}[][] {name};')
                    elif is_arr:
                        if item.init:
                            self.emit(f'{prefix} {jt_}[] {name} = {self._e(item.init)};')
                        elif sz:
                            self.emit(f'{prefix} {jt_}[] {name} = new {jt_}[{sz}];')
                        else:
                            self.emit(f'{prefix} {jt_}[] {name};')
                    else:
                        if item.init:
                            self.emit(f'{prefix} {jt_} {name} = {self._e(item.init)};')
                        else:
                            self.emit(f'{prefix} {jt_} {name};')
            elif isinstance(item, c_ast.Typedef):
                pass  # skip typedefs for now

        self.indent = 0
        self.emit('}')

    # ── Enum ──────────────────────────────────────────────────────────────────
    def _enum_decl(self, item):
        enum = item.type
        name = enum.name or item.name or 'AnEnum'
        vals = []
        if enum.values:
            for ev in enum.values.enumerators:
                if ev.value:
                    vals.append(f'{ev.name} = {self._e(ev.value)}')
                else:
                    vals.append(ev.name)
        # Java enum doesn't support = value directly, so we use constants
        # For simple enums (no values), use real enum; otherwise use int constants
        has_values = any('=' in v for v in vals)
        if has_values:
            for v in vals:
                parts = v.split(' = ')
                if len(parts) == 2:
                    self.emit(f'static final int {parts[0].strip()} = {parts[1].strip()};')
                else:
                    self.emit(f'static final int {v.strip()};')
        else:
            # Clean enum
            members = ', '.join(v.strip() for v in vals)
            self.emit(f'enum {name} {{ {members} }}')
        self.blank()

    # ── Struct → inner class ──────────────────────────────────────────────────
    def _struct_decl(self, item):
        struct = item.type
        name = struct.name or item.name or 'AStruct'
        self.emit(f'static class {name} {{')
        self.indent += 1
        if struct.decls:
            for d in struct.decls:
                jt_, fn, is_arr, sz, is_2d, sz2 = _extract(d)
                if is_2d:
                    self.emit(f'{jt_}[][] {fn};')
                elif is_arr:
                    if sz:
                        self.emit(f'{jt_}[] {fn} = new {jt_}[{sz}];')
                    else:
                        self.emit(f'{jt_}[] {fn};')
                else:
                    self.emit(f'{jt_} {fn};')
        self.indent -= 1
        self.emit('}')
        self.blank()

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
            if isinstance(p, c_ast.EllipsisParam):
                parts.append('Object... _va')
                continue
            jt_, nm, is_arr, _, is_2d, _ = _extract(p)
            if is_2d:
                parts.append(f'{jt_}[][] {nm}')
            elif is_arr:
                parts.append(f'{jt_}[] {nm}')
            else:
                parts.append(f'{jt_} {nm}')
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
        elif isinstance(n, c_ast.Label):
            self.emit(f'{n.name}:')
            if n.stmt: self._stmt(n.stmt)
        elif isinstance(n, c_ast.Goto):
            self.emit(f'/* goto {n.name}; */ break; // goto not supported')
        elif isinstance(n, c_ast.Compound):
            self.indent+=1; self.visit_Compound(n); self.indent-=1
        elif isinstance(n, c_ast.EmptyStatement):
            pass  # skip empty statements
        else:
            self.emit(f'/* unsupported: {type(n).__name__} */')

    def _local(self, d):
        # Handle enum declarations locally
        if isinstance(d.type, c_ast.Enum):
            self._enum_decl(d)
            return
        # Handle struct declarations locally
        if isinstance(d.type, c_ast.Struct):
            self._struct_decl(d)
            return

        jt_, nm, is_arr, sz, is_2d, sz2 = _extract(d)
        is_const = _is_const(d)
        prefix = 'final ' if is_const else ''

        if is_2d:
            if d.init and isinstance(d.init, c_ast.InitList):
                # 2D init: {{1,2},{3,4}}
                rows = []
                for expr in d.init.exprs:
                    rows.append(self._e(expr))
                vals = ', '.join(rows)
                self.emit(f'{prefix}{jt_}[][] {nm} = {{{vals}}};')
            elif sz and sz2:
                self.emit(f'{prefix}{jt_}[][] {nm} = new {jt_}[{sz}][{sz2}];')
            else:
                self.emit(f'{prefix}{jt_}[][] {nm};')
        elif is_arr:
            if d.init and isinstance(d.init, c_ast.InitList):
                vals = ', '.join(self._e(e) for e in d.init.exprs)
                self.emit(f'{prefix}{jt_}[] {nm} = {{{vals}}};')
            elif d.init:
                # Non-InitList init (e.g. malloc) — use expression directly
                self.emit(f'{prefix}{jt_}[] {nm} = {self._e(d.init)};')
            elif sz:
                self.emit(f'{prefix}{jt_}[] {nm} = new {jt_}[{sz}];')
            else:
                self.emit(f'{prefix}{jt_}[] {nm};')
        else:
            if d.init: self.emit(f'{prefix}{jt_} {nm} = {self._e(d.init)};')
            else:      self.emit(f'{prefix}{jt_} {nm};')

    def _if(self, n):
        self.emit(f'if ({self._e(n.cond)}) {{')
        self.indent+=1; self._stmt(n.iftrue); self.indent-=1
        if n.iffalse:
            if isinstance(n.iffalse, c_ast.If):
                cond2 = self._e(n.iffalse.cond)
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
                    jt_, nm, _, _, _, _ = _extract(d)
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

        if name == 'puts':
            self.emit(f'System.out.println({args[0] if args else ""});')
            return

        if name == 'putchar':
            self.emit(f'System.out.print((char){args[0]});')
            return

        if name == 'exit':
            self.emit(f'System.exit({args[0] if args else "0"});')
            return

        if name == 'srand':
            self.emit(f'/* srand({args[0] if args else ""}) -- Java uses Math.random() */;')
            return

        if name == 'free':
            self.emit(f'/* free({args[0] if args else ""}) -- Java has GC */;')
            return

        if name == 'scanf':
            fmt   = args[0].strip('"') if args else ''
            vars_ = args[1:]
            specs = []
            i = 0
            while i < len(fmt):
                if fmt[i]=='%' and i+1<len(fmt):
                    # Handle longer format specs like %ld, %lf
                    end = i+2
                    if end < len(fmt) and fmt[end] in 'dfilscu':
                        end += 1
                    specs.append(fmt[i:end]); i=end
                else: i+=1
            for idx, var in enumerate(vars_):
                vn  = var.lstrip('&')
                sp  = specs[idx] if idx<len(specs) else '%d'
                if sp in ('%d','%i','%ld'):  self.emit(f'{vn} = sc.nextInt();')
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
