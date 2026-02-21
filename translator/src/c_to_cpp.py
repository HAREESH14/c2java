# =============================================================================
#  c_to_cpp.py  -- C -> C++ translator (enhanced)
#
#  Uses: pycparser (C AST)  ->  C++ source strings
#
#  Translation map:
#    printf -> cout <<, scanf -> cin >>,
#    char*/char[] -> std::string, malloc/free -> new/delete,
#    struct -> class, enum -> enum class,
#    strcmp -> .compare(), strlen -> .length(), strcat -> +,
#    puts -> cout <<, exit -> exit, NULL -> nullptr,
#    sprintf -> ostringstream, fprintf -> ofstream <<,
#    fopen/fclose -> ifstream/ofstream, memcpy -> copy,
#    memset -> fill, qsort -> sort, typedef -> using,
#    getchar -> cin.get(), putchar -> cout.put(),
#    function pointers -> std::function
# =============================================================================

import pycparser
from pycparser import c_ast

TYPE_MAP = {
    'int':'int','float':'float','double':'double','char':'char',
    'void':'void','long':'long','short':'short','unsigned':'int',
    'bool':'bool','_Bool':'bool','size_t':'size_t',
}

# C library functions -> C++ equivalents
MATH_FUNCS = {
    'sqrt','pow','sin','cos','tan','asin','acos','atan','atan2',
    'ceil','floor','round','log','log10','exp','abs','fabs','fmax','fmin',
}

def _cpptype(ct):
    return TYPE_MAP.get(ct, ct)


class ExprVisitor(c_ast.NodeVisitor):

    def visit_Constant(self, n):
        v = n.value
        if v == 'NULL': return 'nullptr'
        if n.type == 'string':
            return f'string({v})'  # wrap in string()
        return v

    def visit_ID(self, n):
        if n.name == 'NULL': return 'nullptr'
        if n.name == 'true' or n.name == 'false': return n.name
        if n.name == 'M_PI': return 'M_PI'
        if n.name == 'M_E': return 'M_E'
        return n.name

    def visit_BinaryOp(self, n):
        return f'({self.visit(n.left)} {n.op} {self.visit(n.right)})'

    def visit_UnaryOp(self, n):
        e, op = self.visit(n.expr), n.op
        if op == 'p++': return f'{e}++'
        if op == 'p--': return f'{e}--'
        if op == 'sizeof': return f'sizeof({e})'
        if op in ('&','*'): return f'{op}{e}'
        return f'{op}{e}'

    def visit_Assignment(self, n):
        return f'{self.visit(n.lvalue)} {n.op} {self.visit(n.rvalue)}'

    def visit_FuncCall(self, n):
        name = n.name.name if isinstance(n.name, c_ast.ID) else self.visit(n.name)
        args = [self.visit(a) for a in (n.args.exprs if n.args else [])]

        # printf -> cout <<
        if name == 'printf':
            return self._printf_to_cout(args)
        if name == 'fprintf':
            # fprintf(fp, fmt, ...) -> fp << fmt
            if len(args) >= 2:
                return f'{args[0]} << {args[1]}'
            return f'{args[0]} << ""'
        if name == 'puts':
            return f'cout << {args[0]} << endl'
        if name == 'putchar':
            return f'cout.put({args[0]})'

        # scanf -> cin >>
        if name == 'scanf':
            return self._scanf_to_cin(args)
        if name == 'fscanf':
            if len(args) >= 3:
                return f'{args[0]} >> {args[2].lstrip("&")}'
            return f'/* fscanf */'

        # malloc -> new
        if name == 'malloc':
            return f'new int[{args[0] if args else "10"}]'
        if name == 'calloc':
            return f'new int[{args[0] if args else "10"}]()'
        if name == 'free':
            return f'delete[] {args[0]}'
        if name == 'realloc':
            return f'/* realloc: use vector */ {args[0]}'

        # exit
        if name == 'exit':
            return f'exit({args[0] if args else "0"})'
        if name == 'abort':
            return 'abort()'

        # ── File I/O: fopen -> ifstream/ofstream ──
        if name == 'fopen':
            # fopen(path, mode) -> ifstream(path) or ofstream(path)
            if len(args) >= 2:
                mode = args[1].strip('"')
                if 'w' in mode or 'a' in mode:
                    return f'new ofstream({args[0]})'
                return f'new ifstream({args[0]})'
            return f'new ifstream({args[0] if args else ""})'
        if name == 'fclose':
            return f'{args[0]}->close()'
        if name == 'fread':
            return f'{args[3] if len(args)>3 else "fin"}.read((char*){args[0]}, {args[1]} * {args[2]})'
        if name == 'fwrite':
            return f'{args[3] if len(args)>3 else "fout"}.write((char*){args[0]}, {args[1]} * {args[2]})'
        if name == 'fgets':
            if len(args) >= 3:
                return f'getline({args[2]}, {args[0]})'
            return f'getline(cin, {args[0] if args else ""})'
        if name == 'fputs':
            if len(args) >= 2:
                return f'{args[1]} << {args[0]}'
            return f'cout << {args[0] if args else ""}'

        # ── sprintf -> ostringstream ──
        if name == 'sprintf':
            if len(args) >= 2:
                return f'/* sprintf: use ostringstream */ sprintf({args[0]}, {", ".join(args[1:])})'
            return f'/* sprintf */'
        if name == 'snprintf':
            if len(args) >= 3:
                return f'/* snprintf: use ostringstream */ snprintf({", ".join(args)})'
            return f'/* snprintf */'

        # ── String functions -> C++ methods ──
        if name == 'strlen':
            return f'{args[0]}.length()'
        if name == 'strcmp':
            return f'{args[0]}.compare({args[1]})'
        if name == 'strncmp':
            return f'{args[0]}.compare(0, {args[2]}, {args[1]})'
        if name == 'strcpy':
            return f'{args[0]} = {args[1]}'
        if name == 'strncpy':
            return f'{args[0]} = {args[1]}.substr(0, {args[2]})'
        if name == 'strcat':
            return f'{args[0]} += {args[1]}'
        if name == 'strncat':
            return f'{args[0]} += {args[1]}.substr(0, {args[2]})'
        if name == 'strstr':
            return f'({args[0]}.find({args[1]}) != string::npos)'
        if name == 'strchr':
            return f'({args[0]}.find({args[1]}) != string::npos)'
        if name == 'strrchr':
            return f'({args[0]}.rfind({args[1]}) != string::npos)'
        if name == 'strdup':
            return f'string({args[0]})'
        if name == 'strtok':
            return f'/* strtok: use stringstream */ strtok({", ".join(args)})'

        # ── Type conversion ──
        if name == 'atoi': return f'stoi({args[0]})'
        if name == 'atof': return f'stod({args[0]})'
        if name == 'atol': return f'stol({args[0]})'

        # ── Memory functions -> C++ algorithms ──
        if name == 'memcpy':
            return f'copy({args[1]}, {args[1]} + {args[2]}, {args[0]})'
        if name == 'memmove':
            return f'copy({args[1]}, {args[1]} + {args[2]}, {args[0]})'
        if name == 'memset':
            return f'fill({args[0]}, {args[0]} + {args[2]}, {args[1]})'
        if name == 'memcmp':
            return f'equal({args[0]}, {args[0]} + {args[2]}, {args[1]})'

        # ── qsort -> sort ──
        if name == 'qsort':
            return f'sort({args[0]}, {args[0]} + {args[1]})'

        # ── bsearch -> lower_bound (simplified) ──
        if name == 'bsearch':
            return f'/* bsearch: use lower_bound */ lower_bound({args[1]}, {args[1]} + {args[2]}, *{args[0]})'

        # ── Character functions ──
        if name in ('toupper','tolower','isalpha','isdigit','isspace','isalnum','isupper','islower'):
            return f'{name}({", ".join(args)})'

        # ── rand/srand ──
        if name == 'rand':  return 'rand()'
        if name == 'srand': return f'srand({args[0] if args else "time(0)"})'

        # ── I/O ──
        if name == 'getchar': return 'cin.get()'
        if name == 'getc':    return f'{args[0]}.get()' if args else 'cin.get()'
        if name == 'ungetc':  return f'{args[1]}.putback({args[0]})' if len(args) >= 2 else f'cin.putback({args[0]})'

        # ── assert ──
        if name == 'assert': return f'assert({", ".join(args)})'

        # ── Math functions — keep as-is (cmath) ──
        if name in MATH_FUNCS:
            return f'{name}({", ".join(args)})'

        return f'{name}({", ".join(args)})'

    def _printf_to_cout(self, args):
        if not args: return 'cout << endl'
        fmt = args[0]
        # Check if it's a string literal
        if fmt.startswith('string('):
            fmt = fmt[7:-1]  # remove string() wrapper
        if not fmt.startswith('"'):
            return f'cout << {fmt}'

        # Parse format string and build cout chain
        fmt_str = fmt[1:-1]  # remove quotes
        rest = args[1:]
        parts = []
        i = 0
        arg_idx = 0
        current_str = ''
        while i < len(fmt_str):
            if fmt_str[i] == '%' and i+1 < len(fmt_str):
                if current_str:
                    parts.append(f'"{current_str}"')
                    current_str = ''
                spec = fmt_str[i+1]
                if spec == 'n':
                    parts.append('endl')
                    i += 2
                    continue
                elif spec == '%':
                    current_str += '%'
                    i += 2
                    continue
                # Skip format specifier chars
                j = i + 1
                while j < len(fmt_str) and fmt_str[j] in 'diouxXeEfgGaAcspnlhqjzt.0123456789-+ #*L':
                    j += 1
                if arg_idx < len(rest):
                    parts.append(rest[arg_idx])
                    arg_idx += 1
                i = j
            elif fmt_str[i:i+2] == '\\n':
                if current_str:
                    parts.append(f'"{current_str}"')
                    current_str = ''
                parts.append('endl')
                i += 2
            else:
                current_str += fmt_str[i]
                i += 1
        if current_str:
            parts.append(f'"{current_str}"')

        if not parts:
            return 'cout << endl'
        return 'cout << ' + ' << '.join(parts)

    def _scanf_to_cin(self, args):
        if len(args) < 2: return f'cin >> /* scanf */'
        vars_ = args[1:]
        parts = []
        for v in vars_:
            vn = v.lstrip('&')
            parts.append(vn)
        return 'cin >> ' + ' >> '.join(parts)

    def visit_ArrayRef(self, n):
        return f'{self.visit(n.name)}[{self.visit(n.subscript)}]'

    def visit_StructRef(self, n):
        op = n.type  # '.' or '->'
        return f'{self.visit(n.name)}{op}{n.field.name}'

    def visit_Cast(self, n):
        t = _gtype(n.to_type.type)
        return f'static_cast<{_cpptype(t)}>({self.visit(n.expr)})'

    def visit_TernaryOp(self, n):
        return f'({self.visit(n.cond)} ? {self.visit(n.iftrue)} : {self.visit(n.iffalse)})'

    def visit_InitList(self, n):
        return '{' + ', '.join(self.visit(e) for e in n.exprs) + '}'

    def visit_ExprList(self, n):
        return ', '.join(self.visit(e) for e in n.exprs)

    def generic_visit(self, n):
        return f'/* expr:{type(n).__name__} */'


def _gtype(t):
    if isinstance(t, c_ast.TypeDecl):       return _gtype(t.type)
    if isinstance(t, c_ast.IdentifierType): return ' '.join(t.names)
    if isinstance(t, (c_ast.PtrDecl, c_ast.ArrayDecl, c_ast.FuncDecl)):
        return _gtype(t.type)
    return 'void'


def _is_const(decl):
    if hasattr(decl, 'quals') and decl.quals and 'const' in decl.quals:
        return True
    if hasattr(decl, 'type'):
        t = decl.type
        if hasattr(t, 'quals') and t.quals and 'const' in t.quals:
            return True
    return False


def _extract(decl):
    """Extract (cpp_type, name, is_arr, arr_sz, is_2d, sz2) from a C declaration."""
    name   = decl.name
    dtype  = decl.type
    is_arr = False
    arr_sz = None
    is_2d  = False
    sz2    = None
    ev     = ExprVisitor()

    if isinstance(dtype, c_ast.ArrayDecl):
        if isinstance(dtype.type, c_ast.ArrayDecl):
            is_2d = True
            arr_sz = ev.visit(dtype.dim) if dtype.dim else None
            sz2    = ev.visit(dtype.type.dim) if dtype.type.dim else None
            inner  = _gtype(dtype.type.type)
            if inner == 'char':
                return ('string', name, True, arr_sz, False, None)
            return (_cpptype(inner), name, True, arr_sz, True, sz2)
        inner = _gtype(dtype.type)
        if inner == 'char':
            return ('string', name, False, None, False, None)
        is_arr = True
        arr_sz = ev.visit(dtype.dim) if dtype.dim else None
        dtype  = dtype.type
    elif isinstance(dtype, c_ast.PtrDecl):
        inner  = _gtype(dtype.type)
        if inner == 'char':
            return ('string', name, False, None, False, None)
        is_arr = True
        dtype  = dtype.type

    ts = _gtype(dtype)
    return (_cpptype(ts), name, is_arr, arr_sz, is_2d, sz2)


def _uses_scanf(node):
    class F(c_ast.NodeVisitor):
        found = False
        def visit_FuncCall(self, n):
            if isinstance(n.name, c_ast.ID) and n.name.name == 'scanf':
                self.found = True
            self.generic_visit(n)
    f = F(); f.visit(node); return f.found


def _uses_strings(node):
    class F(c_ast.NodeVisitor):
        found = False
        def visit_Decl(self, n):
            if isinstance(n.type, c_ast.ArrayDecl):
                if _gtype(n.type.type) == 'char': self.found = True
            elif isinstance(n.type, c_ast.PtrDecl):
                if _gtype(n.type.type) == 'char': self.found = True
            self.generic_visit(n)
    f = F(); f.visit(node); return f.found


def _uses_file_io(node):
    class F(c_ast.NodeVisitor):
        found = False
        def visit_FuncCall(self, n):
            if isinstance(n.name, c_ast.ID) and n.name.name in ('fopen','fclose','fread','fwrite','fgets','fputs','fprintf','fscanf'):
                self.found = True
            self.generic_visit(n)
    f = F(); f.visit(node); return f.found

def _uses_algorithm(node):
    class F(c_ast.NodeVisitor):
        found = False
        def visit_FuncCall(self, n):
            if isinstance(n.name, c_ast.ID) and n.name.name in ('qsort','bsearch','memcpy','memmove','memset','memcmp'):
                self.found = True
            self.generic_visit(n)
    f = F(); f.visit(node); return f.found


# ---------------------------------------------------------------------------
class CToCppVisitor(c_ast.NodeVisitor):

    def __init__(self):
        self.indent  = 0
        self.output  = []
        self.uses_io = False
        self.uses_string = False
        self.uses_math = False
        self.uses_vector = False
        self.uses_fstream = False
        self.uses_algorithm = False

    def ind(self): return '    ' * self.indent
    def emit(self, s): self.output.append(self.ind() + s)
    def blank(self): self.output.append('')
    def result(self): return '\n'.join(self.output)
    def _e(self, n): return ExprVisitor().visit(n)

    def visit_FileAST(self, node):
        self.uses_io = True
        self.uses_string = _uses_strings(node)
        self.uses_math = any(f in str(node) for f in MATH_FUNCS)
        self.uses_fstream = _uses_file_io(node)
        self.uses_algorithm = _uses_algorithm(node)

        # Emit includes
        self.emit('#include <iostream>')
        if self.uses_string:    self.emit('#include <string>')
        if self.uses_math:      self.emit('#include <cmath>')
        if self.uses_fstream:   self.emit('#include <fstream>')
        if self.uses_algorithm: self.emit('#include <algorithm>')
        self.emit('#include <cstdlib>')
        self.blank()
        self.emit('using namespace std;')
        self.blank()

        for item in node.ext:
            if isinstance(item, c_ast.FuncDef):
                self._func_def(item)
                self.blank()
            elif isinstance(item, c_ast.Decl):
                if isinstance(item.type, c_ast.Struct):
                    self._struct(item)
                elif isinstance(item.type, c_ast.Enum):
                    self._enum(item)
                elif isinstance(item.type, c_ast.FuncDecl):
                    self._fwd_decl(item)
                else:
                    self._global_var(item)
            elif isinstance(item, c_ast.Typedef):
                self._typedef(item)

    def _fwd_decl(self, item):
        name = item.name
        ftype = item.type
        ret = _cpptype(_gtype(ftype.type))
        params = self._params(ftype.args) if ftype.args else ''
        self.emit(f'{ret} {name}({params});')

    def _global_var(self, item):
        t, name, is_arr, sz, is_2d, sz2 = _extract(item)
        is_const = _is_const(item)
        prefix = 'const ' if is_const else ''
        if is_2d:
            if sz and sz2:
                self.emit(f'{prefix}{t} {name}[{sz}][{sz2}];')
            else:
                self.emit(f'{prefix}{t} {name}[][];')
        elif is_arr:
            if item.init:
                self.emit(f'{prefix}{t} {name}[] = {self._e(item.init)};')
            elif sz:
                self.emit(f'{prefix}{t} {name}[{sz}];')
            else:
                self.emit(f'{prefix}{t} *{name};')
        else:
            if item.init:
                self.emit(f'{prefix}{t} {name} = {self._e(item.init)};')
            else:
                self.emit(f'{prefix}{t} {name};')

    def _struct(self, item):
        struct = item.type
        name = struct.name or item.name or 'MyStruct'
        self.emit(f'class {name} {{')
        self.emit('public:')
        self.indent += 1
        if struct.decls:
            for d in struct.decls:
                t, fn, is_arr, sz, _, _ = _extract(d)
                if is_arr:
                    if sz: self.emit(f'{t} {fn}[{sz}];')
                    else:  self.emit(f'{t}* {fn};')
                else:
                    self.emit(f'{t} {fn};')
        self.indent -= 1
        self.emit('};')
        self.blank()

    def _enum(self, item):
        enum = item.type
        name = enum.name or item.name or 'MyEnum'
        vals = []
        if enum.values:
            for ev in enum.values.enumerators:
                if ev.value:
                    vals.append(f'{ev.name} = {self._e(ev.value)}')
                else:
                    vals.append(ev.name)
        # Use enum class (scoped enum) for modern C++
        self.emit(f'enum class {name} {{ {", ".join(vals)} }};')
        self.blank()

    def _typedef(self, item):
        """Translate C typedef to C++ using declaration."""
        name = item.name
        inner = _gtype(item.type)
        self.emit(f'using {name} = {_cpptype(inner)};')

    def _func_def(self, node):
        fname = node.decl.name
        ftype = node.decl.type
        ret   = _cpptype(_gtype(ftype.type))
        params = 'int argc, char* argv[]' if fname == 'main' and ret == 'int' else (
            self._params(ftype.args) if ftype.args else '')
        # Keep main as int main
        self.emit(f'{ret} {fname}({params}) {{')
        self.indent += 1
        self._compound(node.body)
        self.indent -= 1
        self.emit('}')

    def _params(self, pl):
        parts = []
        for p in pl.params:
            if isinstance(p, c_ast.EllipsisParam):
                parts.append('...')
                continue
            t, nm, is_arr, _, _, _ = _extract(p)
            if is_arr:
                parts.append(f'{t} {nm}[]')
            else:
                parts.append(f'{t} {nm}')
        return ', '.join(parts)

    def _compound(self, n):
        if n and n.block_items:
            for s in n.block_items:
                self._stmt(s)

    def _stmt(self, n):
        if isinstance(n, c_ast.Decl):       self._local(n)
        elif isinstance(n, c_ast.If):       self._if(n)
        elif isinstance(n, c_ast.For):      self._for(n)
        elif isinstance(n, c_ast.While):    self._while(n)
        elif isinstance(n, c_ast.DoWhile):  self._dowhile(n)
        elif isinstance(n, c_ast.Return):   self._return(n)
        elif isinstance(n, c_ast.FuncCall): self._call_stmt(n)
        elif isinstance(n, c_ast.Assignment):
            self.emit(f'{self._e(n.lvalue)} {n.op} {self._e(n.rvalue)};')
        elif isinstance(n, c_ast.UnaryOp):  self.emit(f'{self._e(n)};')
        elif isinstance(n, c_ast.Break):    self.emit('break;')
        elif isinstance(n, c_ast.Continue): self.emit('continue;')
        elif isinstance(n, c_ast.Switch):   self._switch(n)
        elif isinstance(n, c_ast.Compound):
            self.indent += 1; self._compound(n); self.indent -= 1
        elif isinstance(n, c_ast.Label):
            self.emit(f'{n.name}:')
            if n.stmt: self._stmt(n.stmt)
        elif isinstance(n, c_ast.Goto):
            self.emit(f'goto {n.name};')
        elif isinstance(n, c_ast.EmptyStatement):
            pass
        else:
            self.emit(f'// unsupported: {type(n).__name__}')

    def _local(self, d):
        if isinstance(d.type, c_ast.Struct):
            self._struct(d); return
        if isinstance(d.type, c_ast.Enum):
            self._enum(d); return

        t, nm, is_arr, sz, is_2d, sz2 = _extract(d)
        is_const = _is_const(d)
        prefix = 'const ' if is_const else ''

        if is_2d:
            if d.init:
                self.emit(f'{prefix}{t} {nm}[][{sz2 or ""}] = {self._e(d.init)};')
            elif sz and sz2:
                self.emit(f'{prefix}{t} {nm}[{sz}][{sz2}];')
            else:
                self.emit(f'{prefix}{t} {nm}[][];')
        elif is_arr:
            if d.init and isinstance(d.init, c_ast.InitList):
                self.emit(f'{prefix}{t} {nm}[] = {self._e(d.init)};')
            elif d.init:
                self.emit(f'{prefix}{t}* {nm} = {self._e(d.init)};')
            elif sz:
                self.emit(f'{prefix}{t} {nm}[{sz}];')
            else:
                self.emit(f'{prefix}{t}* {nm};')
        else:
            if t == 'string' and d.init:
                init_val = self._e(d.init)
                # Remove the string() wrapper for direct assignment
                if init_val.startswith('string(') and init_val.endswith(')'):
                    init_val = init_val[7:-1]
                self.emit(f'{prefix}string {nm} = {init_val};')
            elif d.init:
                self.emit(f'{prefix}{t} {nm} = {self._e(d.init)};')
            else:
                self.emit(f'{prefix}{t} {nm};')

    def _if(self, n):
        self.emit(f'if ({self._e(n.cond)}) {{')
        self.indent += 1; self._stmt(n.iftrue); self.indent -= 1
        if n.iffalse:
            if isinstance(n.iffalse, c_ast.If):
                cond2 = self._e(n.iffalse.cond)
                prev = self.output.pop() if self.output and self.output[-1].strip() == '}' else None
                if prev: self.output.append(self.ind() + f'}} else if ({cond2}) {{')
                else:    self.emit(f'}} else if ({cond2}) {{')
                self.indent += 1; self._stmt(n.iffalse.iftrue); self.indent -= 1
                if n.iffalse.iffalse:
                    self.emit('} else {')
                    self.indent += 1; self._stmt(n.iffalse.iffalse); self.indent -= 1
                self.emit('}')
            else:
                self.emit('} else {')
                self.indent += 1; self._stmt(n.iffalse); self.indent -= 1
                self.emit('}')
        else:
            self.emit('}')

    def _for(self, n):
        init_s = ''
        if n.init:
            if isinstance(n.init, c_ast.DeclList):
                parts = []
                for d in n.init.decls:
                    t_, nm_, _, _, _, _ = _extract(d)
                    iv = self._e(d.init) if d.init else '0'
                    parts.append(f'{t_} {nm_} = {iv}')
                init_s = ', '.join(parts)
            else:
                init_s = self._e(n.init).rstrip(';')
        cond_s = self._e(n.cond) if n.cond else ''
        next_s = self._e(n.next) if n.next else ''
        self.emit(f'for ({init_s}; {cond_s}; {next_s}) {{')
        self.indent += 1
        if isinstance(n.stmt, c_ast.Compound): self._compound(n.stmt)
        else: self._stmt(n.stmt)
        self.indent -= 1; self.emit('}')

    def _while(self, n):
        self.emit(f'while ({self._e(n.cond)}) {{')
        self.indent += 1
        if isinstance(n.stmt, c_ast.Compound): self._compound(n.stmt)
        else: self._stmt(n.stmt)
        self.indent -= 1; self.emit('}')

    def _dowhile(self, n):
        self.emit('do {')
        self.indent += 1
        if isinstance(n.stmt, c_ast.Compound): self._compound(n.stmt)
        else: self._stmt(n.stmt)
        self.indent -= 1; self.emit(f'}} while ({self._e(n.cond)});')

    def _return(self, n):
        if n.expr:
            self.emit(f'return {self._e(n.expr)};')
        else:
            self.emit('return;')

    def _switch(self, n):
        self.emit(f'switch ({self._e(n.cond)}) {{')
        self.indent += 1
        if isinstance(n.stmt, c_ast.Compound) and n.stmt.block_items:
            for item in n.stmt.block_items:
                if isinstance(item, c_ast.Case):
                    self.emit(f'case {self._e(item.expr)}:')
                    self.indent += 1
                    for s in (item.stmts or []): self._stmt(s)
                    self.indent -= 1
                elif isinstance(item, c_ast.Default):
                    self.emit('default:')
                    self.indent += 1
                    for s in (item.stmts or []): self._stmt(s)
                    self.indent -= 1
        self.indent -= 1; self.emit('}')

    def _call_stmt(self, n):
        name = n.name.name if isinstance(n.name, c_ast.ID) else self._e(n.name)
        args = [self._e(a) for a in (n.args.exprs if n.args else [])]

        if name == 'printf':
            self.emit(self._e(n) + ';')
            return
        if name == 'fprintf':
            if len(args) >= 2:
                self.emit(f'{args[0]} << {args[1]};')
            return
        if name == 'puts':
            self.emit(f'cout << {args[0]} << endl;')
            return
        if name == 'putchar':
            self.emit(f'cout.put({args[0]});')
            return
        if name == 'scanf':
            cin_expr = ExprVisitor()._scanf_to_cin(args)
            self.emit(f'{cin_expr};')
            return
        if name == 'free':
            self.emit(f'delete[] {args[0]};')
            return
        if name == 'fclose':
            self.emit(f'{args[0]}->close();')
            return
        if name == 'srand':
            self.emit(f'srand({args[0] if args else "time(0)"});')
            return

        self.emit(f'{self._e(n)};')


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------
def translate_string(c_source: str) -> str:
    parser = pycparser.CParser()
    try:
        ast = parser.parse(c_source, filename='<string>')
    except pycparser.plyparser.ParseError as e:
        raise ValueError(f'C parse error: {e}') from e
    v = CToCppVisitor()
    v.visit(ast)
    return v.result()


def translate_file(c_path: str) -> str:
    import re, os
    fake = os.path.join(os.path.dirname(pycparser.__file__), 'utils', 'fake_libc_include')
    try:
        ast = pycparser.parse_file(c_path, use_cpp=True,
                                   cpp_path='gcc', cpp_args=['-E', f'-I{fake}'])
        v = CToCppVisitor(); v.visit(ast); return v.result()
    except Exception:
        pass
    with open(c_path, encoding='utf-8') as f:
        src = f.read()
    src = re.sub(r'//.*?$|/\*.*?\*/', '', src, flags=re.M | re.S)
    src = '\n'.join(l for l in src.splitlines() if not l.strip().startswith('#'))
    return translate_string(src)
