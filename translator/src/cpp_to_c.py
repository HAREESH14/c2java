# =============================================================================
#  cpp_to_c.py  -- C++ -> C translator (AST-based)
#
#  Uses: tree-sitter with tree-sitter-cpp for real C++ AST parsing
#
#  Translation map:
#    cout << -> printf,  cin >> -> scanf,
#    string -> char*,  bool -> int,  true/false -> 1/0,
#    new/delete -> malloc/free,  class -> struct,
#    #include <iostream> -> #include <stdio.h>,
#    namespace -> stripped,  nullptr -> NULL,
#    endl -> \n,  stoi -> atoi,  string methods -> C string funcs,
#    static_cast -> (type),  references -> pointers
# =============================================================================

import tree_sitter_cpp as tscpp
from tree_sitter import Language, Parser

CPP_LANG = Language(tscpp.language())
_parser  = Parser(CPP_LANG)

# Include mapping
INCLUDE_MAP = {
    'iostream':   ['stdio.h', 'stdlib.h'],
    'cstdio':     ['stdio.h'],
    'cstdlib':    ['stdlib.h'],
    'cstring':    ['string.h'],
    'cmath':      ['math.h'],
    'string':     ['string.h'],
    'cstdint':    ['stdint.h'],
    'cassert':    ['assert.h'],
    'ctime':      ['time.h'],
    'climits':    ['limits.h'],
    'cfloat':     ['float.h'],
    'algorithm':  ['stdlib.h'],     # qsort, bsearch
    'vector':     ['stdlib.h'],
    'map':        [],
    'set':        [],
    'array':      [],
    'fstream':    ['stdio.h'],
    'sstream':    ['stdio.h', 'string.h'],
    'iomanip':    ['stdio.h'],
    'functional': [],
    'memory':     ['stdlib.h'],
    'numeric':    [],
    'utility':    [],
    'stdexcept':  [],
    'typeinfo':   [],
}

# C++ string methods -> C string functions
STRING_METHOD_MAP = {
    'length': 'strlen',
    'size':   'strlen',
    'compare':'strcmp',
    'empty':  None,   # handled specially
    'c_str':  None,   # just return the var
    'find':   'strstr',
    'substr': None,   # handled specially
    'append': 'strcat',
    'at':     None,   # arr[i]
}

# C++ free functions -> C equivalents
FUNC_MAP = {
    'stoi':      'atoi',
    'stod':      'atof',
    'stol':      'atol',
    'stof':      'atof',
    'to_string': None,  # handled specially
}


# ---------------------------------------------------------------------------
def _text(node):
    """Get the text content of a node."""
    return node.text.decode('utf-8') if node.text else ''


def _child_by_type(node, type_name):
    """Find first child with given type."""
    for c in node.children:
        if c.type == type_name:
            return c
    return None


def _children_by_type(node, type_name):
    """Find all children with given type."""
    return [c for c in node.children if c.type == type_name]


def _named_children(node):
    """Get all named (non-anonymous) children."""
    return [c for c in node.children if c.is_named]


# ---------------------------------------------------------------------------
class CppToCTranslator:

    def __init__(self):
        self.indent = 0
        self.output = []
        self.includes = set()
        self.has_scanf = False

    def ind(self): return '    ' * self.indent
    def emit(self, s): self.output.append(self.ind() + s)
    def blank(self): self.output.append('')
    def raw(self, s): self.output.append(s)

    # ── Top level ─────────────────────────────────────────────────────────────
    def translate(self, source: str) -> str:
        tree = _parser.parse(source.encode('utf-8'))
        root = tree.root_node

        # First pass: collect includes and detect features
        body_nodes = []
        for child in root.children:
            if child.type == 'preproc_include':
                self._process_include(child)
            elif child.type == 'using_declaration':
                pass  # skip: using namespace std;
            elif child.type == 'expression_statement':
                txt = _text(child)
                if 'using namespace' in txt:
                    continue  # skip
                body_nodes.append(child)
            else:
                body_nodes.append(child)

        # Emit includes
        for inc in sorted(self.includes):
            self.raw(f'#include <{inc}>')
        if self.includes:
            self.blank()

        # Second pass: translate body
        for child in body_nodes:
            self._top_level(child)

        return '\n'.join(self.output)

    def _process_include(self, node):
        path_node = _child_by_type(node, 'system_lib_string') or _child_by_type(node, 'string_literal')
        if path_node:
            txt = _text(path_node).strip('<>"')
            if txt in INCLUDE_MAP:
                for h in INCLUDE_MAP[txt]:
                    self.includes.add(h)
            else:
                self.includes.add(txt)

    # ── Top-level declarations ──────────────────────────────────────────────
    def _top_level(self, node):
        t = node.type
        if t == 'function_definition':
            self._func_def(node)
            self.blank()
        elif t == 'declaration':
            self._declaration(node, top_level=True)
        elif t == 'class_specifier':
            self._class(node)
        elif t == 'struct_specifier':
            self._struct(node)
        elif t == 'enum_specifier':
            self._enum(node)
        elif t == 'comment':
            self.emit(_text(node))
        elif t == 'preproc_def':
            self.emit(_text(node))
        elif t == 'type_definition':
            self.emit(self._translate_type_text(_text(node)) + ';')
        elif t == 'template_declaration':
            self._template(node)
        elif t == 'namespace_definition':
            # Emit contents without namespace wrapper
            body = _child_by_type(node, 'declaration_list')
            if body:
                for child in body.children:
                    if child.is_named:
                        self._top_level(child)
        elif t == ';' or t == '\n':
            pass
        else:
            txt = _text(node).strip()
            if txt:
                self.emit(self._translate_type_text(txt))

    # ── Class → struct + init/destroy functions ──────────────────────────────────
    def _class(self, node):
        name_node = _child_by_type(node, 'type_identifier')
        name = _text(name_node) if name_node else 'MyClass'
        body = _child_by_type(node, 'field_declaration_list')

        # Check for base class (inheritance)
        base_clause = _child_by_type(node, 'base_class_clause')
        base_class = None
        if base_clause:
            for c in base_clause.children:
                if c.type == 'type_identifier':
                    base_class = _text(c)
                    break

        # Collect fields, constructors, destructors, methods, virtual methods
        fields = []
        constructors = []
        destructor = None
        methods = []
        virtual_methods = []

        if body:
            for child in body.children:
                if child.type == 'access_specifier' or child.type in (':', '{', '}'):
                    continue
                elif child.type == 'field_declaration':
                    txt = _text(child).strip()
                    # Check if it's a virtual function declaration (no body)
                    if 'virtual' in txt:
                        # virtual return_type name(params);
                        virtual_methods.append(('decl', child))
                    else:
                        fields.append(child)
                elif child.type == 'function_definition':
                    decl = _child_by_type(child, 'function_declarator')
                    if decl:
                        # Check for destructor
                        destr = _child_by_type(decl, 'destructor_name')
                        if destr:
                            destructor = child
                            continue
                        # Check for constructor (function name == class name)
                        id_node = _child_by_type(decl, 'identifier') or _child_by_type(decl, 'field_identifier')
                        func_name = _text(id_node) if id_node else ''
                        if func_name == name:
                            constructors.append(child)
                            continue
                    # Check for virtual/override
                    func_txt = _text(child)
                    if 'virtual' in func_txt:
                        virtual_methods.append(('def', child))
                    elif decl and _child_by_type(decl, 'virtual_specifier'):
                        virtual_methods.append(('def', child))
                    else:
                        methods.append(child)
                elif child.type == 'comment':
                    pass  # skip comments in struct

        # ── Emit struct ──
        self.emit(f'typedef struct {{')
        self.indent += 1

        # Base class field (inheritance → composition)
        if base_class:
            self.emit(f'{base_class} base; /* inherits from {base_class} */')

        # Virtual method function pointers
        for kind, vmethod in virtual_methods:
            if kind == 'decl':
                # Parse: virtual return_type name(params);
                txt = _text(vmethod).strip().rstrip(';')
                txt = txt.replace('virtual ', '').strip()
                # Extract return type, name, params
                import re
                m = re.match(r'(\w+)\s+(\w+)\(([^)]*)\)', txt)
                if m:
                    ret_t = self._translate_type(m.group(1))
                    fn_name = m.group(2)
                    params = self._translate_type_text(m.group(3))
                    self.emit(f'{ret_t} (*{fn_name})({name}* self{(", " + params) if params else ""}); /* virtual */')
            elif kind == 'def':
                decl = _child_by_type(vmethod, 'function_declarator')
                if decl:
                    id_node = _child_by_type(decl, 'identifier') or _child_by_type(decl, 'field_identifier')
                    fn_name = _text(id_node) if id_node else 'method'
                    # Get return type
                    ret_t = 'void'
                    for c in vmethod.children:
                        if c.type in ('primitive_type', 'type_identifier'):
                            ret_t = self._translate_type(_text(c))
                            break
                        if c == decl:
                            break
                    # Get params
                    params_node = _child_by_type(decl, 'parameter_list')
                    params = self._translate_params(params_node) if params_node else ''
                    self.emit(f'{ret_t} (*{fn_name})({name}* self{(", " + params) if params else ""}); /* virtual */')

        # Regular fields
        for field in fields:
            self._field_decl(field)

        self.indent -= 1
        self.emit(f'}} {name};')
        self.blank()

        # ── Emit constructor as init function ──
        for ctor in constructors:
            decl = _child_by_type(ctor, 'function_declarator')
            params_node = _child_by_type(decl, 'parameter_list') if decl else None
            params = self._translate_params(params_node) if params_node else ''
            param_str = f'{name}* self' + (f', {params}' if params else '')
            self.emit(f'void {name}_init({param_str}) {{')
            self.indent += 1
            # Handle field initializer list: age(a) -> self->age = a;
            init_list = _child_by_type(ctor, 'field_initializer_list')
            if init_list:
                for init in _children_by_type(init_list, 'field_initializer'):
                    field_id = _child_by_type(init, 'field_identifier')
                    arg_list = _child_by_type(init, 'argument_list')
                    if field_id and arg_list:
                        fname = _text(field_id)
                        args = [_text(c) for c in arg_list.children if c.is_named]
                        arg_val = ', '.join(args) if args else '0'
                        # Check if it's base class init
                        if fname == base_class:
                            self.emit(f'{base_class}_init(({base_class}*)self, {arg_val});')
                        else:
                            self.emit(f'self->{fname} = {self._translate_expr_text(arg_val)};')
            # Constructor body
            body_node = _child_by_type(ctor, 'compound_statement')
            if body_node:
                self._compound(body_node)
            self.indent -= 1
            self.emit('}')
            self.blank()

        # ── Emit destructor as destroy function ──
        if destructor:
            self.emit(f'void {name}_destroy({name}* self) {{')
            self.indent += 1
            body_node = _child_by_type(destructor, 'compound_statement')
            if body_node:
                self._compound(body_node)
            self.indent -= 1
            self.emit('}')
            self.blank()

        # ── Emit regular methods as standalone functions ──
        for method in methods:
            decl = _child_by_type(method, 'function_declarator')
            if not decl:
                continue
            id_node = _child_by_type(decl, 'identifier') or _child_by_type(decl, 'field_identifier')
            fn_name = _text(id_node) if id_node else 'method'
            # Get return type
            ret_t = 'void'
            for c in method.children:
                if c.type in ('primitive_type', 'type_identifier'):
                    ret_t = self._translate_type(_text(c))
                    break
                if c == decl:
                    break
            # Get params
            params_node = _child_by_type(decl, 'parameter_list')
            params = self._translate_params(params_node) if params_node else ''
            param_str = f'{name}* self' + (f', {params}' if params else '')
            self.emit(f'{ret_t} {name}_{fn_name}({param_str}) {{')
            self.indent += 1
            body_node = _child_by_type(method, 'compound_statement')
            if body_node:
                self._compound(body_node)
            self.indent -= 1
            self.emit('}')
            self.blank()

        # ── Emit virtual method implementations ──
        for kind, vmethod in virtual_methods:
            if kind == 'def':
                decl = _child_by_type(vmethod, 'function_declarator')
                if not decl:
                    continue
                id_node = _child_by_type(decl, 'identifier') or _child_by_type(decl, 'field_identifier')
                fn_name = _text(id_node) if id_node else 'method'
                ret_t = 'void'
                for c in vmethod.children:
                    if c.type in ('primitive_type', 'type_identifier'):
                        ret_t = self._translate_type(_text(c))
                        break
                    if c == decl:
                        break
                params_node = _child_by_type(decl, 'parameter_list')
                params = self._translate_params(params_node) if params_node else ''
                param_str = f'{name}* self' + (f', {params}' if params else '')
                self.emit(f'{ret_t} {name}_{fn_name}_impl({param_str}) {{')
                self.indent += 1
                body_node = _child_by_type(vmethod, 'compound_statement')
                if body_node:
                    self._compound(body_node)
                self.indent -= 1
                self.emit('}')
                self.blank()

    def _struct(self, node):
        name_node = _child_by_type(node, 'type_identifier')
        name = _text(name_node) if name_node else 'MyStruct'
        body = _child_by_type(node, 'field_declaration_list')
        self.emit(f'typedef struct {{')
        self.indent += 1
        if body:
            for child in body.children:
                if child.type == 'field_declaration':
                    self._field_decl(child)
                elif child.type == 'comment':
                    self.emit(_text(child))
        self.indent -= 1
        self.emit(f'}} {name};')
        self.blank()

    def _field_decl(self, node):
        txt = _text(node).strip()
        # Remove 'virtual' keyword from field declarations
        txt = txt.replace('virtual ', '')
        txt = self._translate_type_text(txt)
        if not txt.endswith(';'):
            txt += ';'
        self.emit(txt)

    def _enum(self, node):
        self.emit(self._translate_type_text(_text(node)) + ';')
        self.blank()

    # ── Template → #define macro ───────────────────────────────────────────
    def _template(self, node):
        """Translate template<typename T> functions to #define macros."""
        import re
        # Get template params
        tpl_params = _child_by_type(node, 'template_parameter_list')
        type_params = []
        if tpl_params:
            for c in tpl_params.children:
                if c.type == 'type_parameter_declaration':
                    tid = _child_by_type(c, 'type_identifier')
                    if tid:
                        type_params.append(_text(tid))

        # Get the function definition inside
        func = _child_by_type(node, 'function_definition')
        if not func:
            self.emit(f'/* template skipped: {_text(node)[:60]}... */')
            return

        decl = _child_by_type(func, 'function_declarator')
        if not decl:
            self.emit(f'/* template skipped */')
            return

        id_node = _child_by_type(decl, 'identifier')
        fn_name = _text(id_node) if id_node else 'template_fn'

        # Get params
        params_node = _child_by_type(decl, 'parameter_list')
        params = []
        if params_node:
            for c in params_node.children:
                if c.type == 'parameter_declaration':
                    p_id = None
                    for cc in c.children:
                        if cc.type == 'identifier':
                            p_id = _text(cc)
                    if p_id:
                        params.append(p_id)

        # Get body
        body = _child_by_type(func, 'compound_statement')
        body_txt = _text(body).strip() if body else '{ }'
        # Remove { } braces
        if body_txt.startswith('{') and body_txt.endswith('}'):
            body_txt = body_txt[1:-1].strip()

        # Check if it's a simple return expression
        m = re.match(r'return\s+(.+?)\s*;', body_txt)
        if m and len(params) <= 3:
            expr = m.group(1)
            fn_upper = fn_name.upper()
            param_str = ', '.join(params)
            self.emit(f'#define {fn_upper}({param_str}) ({expr})')
        else:
            # Multi-statement: emit as inline-like function with void* or int
            self.emit(f'/* template {fn_name}<{{", ".join(type_params)}}> - complex, emitting as int version */')
            ret_t = 'int'  # default
            p_str = ', '.join(f'int {p}' for p in params)
            self.emit(f'{ret_t} {fn_name}({p_str}) {{')
            self.indent += 1
            if body:
                self._compound(body)
            self.indent -= 1
            self.emit('}')
        self.blank()

    # ── Function definition ──────────────────────────────────────────────────
    def _func_def(self, node):
        # Get the declarator and body
        decl_node = _child_by_type(node, 'function_declarator')
        body_node = _child_by_type(node, 'compound_statement')

        # Get return type
        ret_type = ''
        for child in node.children:
            if child.type in ('primitive_type', 'type_identifier', 'sized_type_specifier', 'qualified_identifier'):
                ret_type = self._translate_type(_text(child))
                break
            if child == decl_node:
                break
            if child.type not in ('comment', '{', '}', 'function_declarator', 'compound_statement'):
                ret_type += _text(child) + ' '

        if not ret_type.strip():
            ret_type = 'void'
        ret_type = self._translate_type(ret_type.strip())

        # Get function name and params
        fname = ''
        params_text = ''
        if decl_node:
            name_node = _child_by_type(decl_node, 'identifier') or _child_by_type(decl_node, 'field_identifier')
            if name_node:
                fname = _text(name_node)
            params_node = _child_by_type(decl_node, 'parameter_list')
            if params_node:
                params_text = self._translate_params(params_node)

        self.emit(f'{ret_type} {fname}({params_text}) {{')
        self.indent += 1
        if body_node:
            self._compound(body_node)
        self.indent -= 1
        self.emit('}')

    def _translate_params(self, node):
        params = []
        for child in node.children:
            if child.type == 'parameter_declaration':
                txt = _text(child)
                txt = self._translate_type_text(txt)
                # Handle references: int& x -> int *x
                txt = txt.replace('&', '*')
                params.append(txt)
            elif child.type == 'variadic_parameter':
                params.append('...')
        return ', '.join(params)

    # ── Compound statement ───────────────────────────────────────────────────
    def _compound(self, node):
        for child in node.children:
            if child.type in ('{', '}'):
                continue
            self._stmt(child)

    # ── Statement dispatcher ─────────────────────────────────────────────────
    def _stmt(self, node):
        t = node.type
        if t == 'declaration':
            self._declaration(node)
        elif t == 'expression_statement':
            self._expr_stmt(node)
        elif t == 'if_statement':
            self._if_stmt(node)
        elif t == 'for_statement':
            self._for_stmt(node)
        elif t == 'for_range_loop':
            self._for_range(node)
        elif t == 'while_statement':
            self._while_stmt(node)
        elif t == 'do_statement':
            self._do_while(node)
        elif t == 'return_statement':
            self._return_stmt(node)
        elif t == 'break_statement':
            self.emit('break;')
        elif t == 'continue_statement':
            self.emit('continue;')
        elif t == 'switch_statement':
            self._switch_stmt(node)
        elif t == 'try_statement':
            self._try_stmt(node)
        elif t == 'throw_statement':
            self.emit(f'/* throw: {self._translate_expr_text(_text(node).strip())} */')
        elif t == 'compound_statement':
            self.emit('{')
            self.indent += 1
            self._compound(node)
            self.indent -= 1
            self.emit('}')
        elif t == 'comment':
            self.emit(_text(node))
        elif t == 'labeled_statement':
            self._labeled_stmt(node)
        elif t == 'goto_statement':
            self.emit(_text(node))
        elif t == ';':
            pass
        else:
            txt = _text(node).strip()
            if txt:
                self.emit(self._translate_expr_text(txt) + ';')

    # ── Declarations ──────────────────────────────────────────────────────────
    def _declaration(self, node, top_level=False):
        txt = _text(node).strip()

        # Check for class/struct/enum inside declaration
        for child in node.children:
            if child.type == 'class_specifier':
                self._class(child)
                return
            if child.type == 'struct_specifier':
                self._struct(child)
                return
            if child.type == 'enum_specifier':
                self._enum(child)
                return

        # Translate the declaration text
        txt = self._translate_type_text(txt)
        txt = self._translate_expr_text(txt)

        if not txt.endswith(';'):
            txt += ';'
        self.emit(txt)

    # ── Expression statement ──────────────────────────────────────────────────
    def _expr_stmt(self, node):
        txt = _text(node).strip()

        # Handle cout << ... ;
        if 'cout' in txt and '<<' in txt:
            self.emit(self._translate_cout(txt))
            return

        # Handle cerr << ... ; -> fprintf(stderr, ...)
        if 'cerr' in txt and '<<' in txt:
            self.includes.add('stdio.h')
            cout_result = self._translate_cout(txt.replace('cerr', 'cout'))
            # Convert printf(...) to fprintf(stderr, ...)
            cout_result = cout_result.replace('printf(', 'fprintf(stderr, ', 1)
            self.emit(cout_result)
            return

        # Handle cin >> ... ;
        if 'cin' in txt and '>>' in txt:
            self.emit(self._translate_cin(txt))
            return

        # Handle ofstream/ifstream method calls
        if ('.open(' in txt or '.close(' in txt or '.write(' in txt or
            '.read(' in txt or '.getline(' in txt):
            self.emit(f'/* fstream: {self._translate_expr_text(txt)} */')
            return

        # General expression
        txt = self._translate_expr_text(txt)
        if not txt.endswith(';'):
            txt += ';'
        self.emit(txt)

    # ── cout -> printf ────────────────────────────────────────────────────────
    def _translate_cout(self, stmt: str) -> str:
        """Translate cout << expr1 << expr2 << endl; to printf(...)."""
        self.includes.add('stdio.h')
        # Remove trailing ;
        stmt = stmt.rstrip(';').strip()

        # Remove leading 'cout' and split by <<
        if 'cout' in stmt:
            idx = stmt.index('cout')
            stmt = stmt[idx + 4:].strip()

        # Remove leading <<
        if stmt.startswith('<<'):
            stmt = stmt[2:].strip()

        parts = [p.strip() for p in stmt.split('<<')]

        fmt_parts = []
        args = []
        for p in parts:
            if p == 'endl':
                fmt_parts.append('\\n')
            elif p.startswith('"') and p.endswith('"'):
                fmt_parts.append(p[1:-1])
            elif p.startswith("'") and p.endswith("'"):
                fmt_parts.append('%c')
                args.append(p)
            elif p.replace('.','',1).replace('-','',1).replace('f','',1).replace('F','',1).isdigit() and '.' in p:
                fmt_parts.append('%f')
                args.append(p)
            elif p.lstrip('-').isdigit():
                fmt_parts.append('%d')
                args.append(p)
            else:
                # Translate variable/expression
                p = self._translate_expr_text(p)
                fmt_parts.append('%d')
                args.append(p)

        fmt_str = ''.join(fmt_parts)
        if args:
            return f'printf("{fmt_str}", {", ".join(args)});'
        else:
            return f'printf("{fmt_str}");'

    # ── cin -> scanf ──────────────────────────────────────────────────────────
    def _translate_cin(self, stmt: str) -> str:
        """Translate cin >> var1 >> var2; to scanf(...)."""
        self.includes.add('stdio.h')
        self.has_scanf = True
        stmt = stmt.rstrip(';').strip()

        if 'cin' in stmt:
            idx = stmt.index('cin')
            stmt = stmt[idx + 3:].strip()
        if stmt.startswith('>>'):
            stmt = stmt[2:].strip()

        vars_ = [v.strip() for v in stmt.split('>>')]
        fmt   = ' '.join(['%d'] * len(vars_))
        addrs = ', '.join(f'&{v}' for v in vars_)
        return f'scanf("{fmt}", {addrs});'

    # ── Control flow ──────────────────────────────────────────────────────────
    def _if_stmt(self, node):
        # Find condition, true body, and else clause directly
        cond = _child_by_type(node, 'condition_clause') or _child_by_type(node, 'parenthesized_expression')
        cond_text = self._translate_expr_text(_text(cond)) if cond else '1'

        self.emit(f'if {cond_text} {{')
        self.indent += 1

        # True body: first compound_statement after condition
        true_body = _child_by_type(node, 'compound_statement')
        if true_body:
            self._compound(true_body)
        else:
            # Single statement (no braces)
            for child in node.children:
                if child.is_named and child != cond and child.type not in ('else_clause',):
                    if child.type not in ('condition_clause', 'parenthesized_expression'):
                        self._stmt(child)
                        break
        self.indent -= 1

        # Else clause
        else_node = _child_by_type(node, 'else_clause')
        if else_node:
            else_children = [c for c in else_node.children if c.is_named]
            if else_children and else_children[0].type == 'if_statement':
                # else if — pop closing brace, emit "} else", recurse
                if self.output and self.output[-1].strip() == '}':
                    self.output.pop()
                self.emit('} else')
                self._if_stmt(else_children[0])
                return
            else:
                self.emit('} else {')
                self.indent += 1
                for child in else_children:
                    if child.type == 'compound_statement':
                        self._compound(child)
                    elif child.is_named:
                        self._stmt(child)
                self.indent -= 1
        self.emit('}')

    def _for_stmt(self, node):
        txt = _text(node)
        import re
        m = re.match(r'for\s*\(([^)]*)\)', txt)
        if m:
            header = self._translate_type_text(self._translate_expr_text(m.group(1)))
            parts = header.split(';')
            if len(parts) == 3:
                self.emit(f'for ({parts[0].strip()}; {parts[1].strip()}; {parts[2].strip()}) {{')
            else:
                self.emit(f'for ({header}) {{')
        else:
            self.emit('for (;;) {')

        self.indent += 1
        body = _child_by_type(node, 'compound_statement')
        if body:
            self._compound(body)
        else:
            for child in node.children:
                if child.type not in ('for', '(', ')', '{', '}', ';') and child.is_named:
                    if child.type != 'compound_statement':
                        self._stmt(child)
        self.indent -= 1
        self.emit('}')

    def _for_range(self, node):
        """Translate range-based for: for(auto x : arr) -> for(int i=0; i<n; i++)"""
        txt = _text(node).strip()
        import re
        # Match: for (type var : collection)
        m = re.match(r'for\s*\(\s*(?:auto|const\s+auto|\w+)\s+(&?)(\w+)\s*:\s*(\w+)\s*\)', txt)
        if m:
            ref = m.group(1)
            var = m.group(2)
            collection = m.group(3)
            self.emit(f'/* range-for over {collection} */')
            self.emit(f'for (int _i = 0; _i < sizeof({collection})/sizeof({collection}[0]); _i++) {{')
            self.indent += 1
            ptr = '*' if ref else ''
            self.emit(f'int {ptr}{var} = {collection}[_i];')
            body = _child_by_type(node, 'compound_statement')
            if body:
                self._compound(body)
            self.indent -= 1
            self.emit('}')
        else:
            self.emit(f'/* unsupported range-for: {txt[:60]} */')

    def _try_stmt(self, node):
        """Translate try/catch: emit try body only, catch as comment."""
        self.emit('/* try */')
        body = _child_by_type(node, 'compound_statement')
        if body:
            self.emit('{')
            self.indent += 1
            self._compound(body)
            self.indent -= 1
            self.emit('}')
        # catch clauses
        for child in node.children:
            if child.type == 'catch_clause':
                catch_txt = _text(child).strip()
                self.emit(f'/* {catch_txt[:80]} */')

    def _while_stmt(self, node):
        cond = _child_by_type(node, 'condition_clause') or _child_by_type(node, 'parenthesized_expression')
        cond_text = self._translate_expr_text(_text(cond)) if cond else '1'
        self.emit(f'while {cond_text} {{')
        self.indent += 1
        body = _child_by_type(node, 'compound_statement')
        if body: self._compound(body)
        self.indent -= 1
        self.emit('}')

    def _do_while(self, node):
        self.emit('do {')
        self.indent += 1
        body = _child_by_type(node, 'compound_statement')
        if body: self._compound(body)
        self.indent -= 1
        # Get condition
        cond = _child_by_type(node, 'parenthesized_expression')
        cond_text = self._translate_expr_text(_text(cond)) if cond else '1'
        self.emit(f'}} while {cond_text};')

    def _return_stmt(self, node):
        txt = _text(node).strip()
        txt = self._translate_expr_text(txt)
        self.emit(txt)

    def _switch_stmt(self, node):
        cond = _child_by_type(node, 'condition_clause') or _child_by_type(node, 'parenthesized_expression')
        cond_text = self._translate_expr_text(_text(cond)) if cond else '0'
        self.emit(f'switch {cond_text} {{')
        self.indent += 1
        body = _child_by_type(node, 'compound_statement')
        if body:
            for child in body.children:
                if child.type == 'case_statement':
                    self._case_stmt(child)
                elif child.type in ('{', '}'):
                    pass
                elif child.is_named:
                    self._stmt(child)
        self.indent -= 1
        self.emit('}')

    def _case_stmt(self, node):
        children = list(node.children)
        # Get case value
        txt = _text(node)
        if txt.strip().startswith('default'):
            self.emit('default:')
        else:
            # Find the value after 'case'
            val = None
            for child in children:
                if child.type not in ('case', ':', 'default') and child.is_named:
                    val = self._translate_expr_text(_text(child))
                    break
            if val:
                self.emit(f'case {val}:')
            else:
                self.emit('case 0:')

        self.indent += 1
        # Emit body statements (skip case/default/: tokens)
        found_colon = False
        for child in children:
            if child.type == ':':
                found_colon = True
                continue
            if found_colon and child.is_named:
                # Handle cout in case statements
                child_txt = _text(child).strip()
                if child.type == 'expression_statement' and 'cout' in child_txt:
                    self.emit(self._translate_cout(child_txt.rstrip(';')))
                elif child.type == 'expression_statement' and 'cin' in child_txt:
                    self.emit(self._translate_cin(child_txt.rstrip(';')))
                else:
                    self._stmt(child)
        self.indent -= 1

    def _labeled_stmt(self, node):
        txt = _text(node).strip()
        self.emit(self._translate_expr_text(txt))

    # ── Type/Expression text translation ──────────────────────────────────────
    def _translate_type(self, t: str) -> str:
        import re
        t = t.strip()
        t = re.sub(r'\bstd::', '', t)
        t = re.sub(r'\bstring\b', 'char*', t)
        t = re.sub(r'\bbool\b', 'int', t)
        t = re.sub(r'\bauto\b', 'int', t)  # simplified
        t = re.sub(r'\bconstexpr\b', 'const', t)
        return t

    def _translate_type_text(self, txt: str) -> str:
        """Translate C++ type keywords in arbitrary text."""
        import re
        txt = re.sub(r'\bstd::', '', txt)
        txt = re.sub(r'\bstring\s+(\w+)\s*=', r'char* \1 =', txt)
        txt = re.sub(r'\bstring\s+(\w+)\s*;', r'char \1[256];', txt)
        txt = re.sub(r'\bstring\b', 'char*', txt)
        txt = re.sub(r'\bbool\b', 'int', txt)
        txt = re.sub(r'\bauto\b', 'int', txt)
        txt = re.sub(r'\bconstexpr\b', 'const', txt)
        # enum class -> enum
        txt = re.sub(r'\benum\s+class\b', 'enum', txt)
        # using Name = Type -> typedef Type Name
        m2 = re.match(r'^(\s*)using\s+(\w+)\s*=\s*(.+?)\s*;', txt)
        if m2:
            txt = f'{m2.group(1)}typedef {m2.group(3)} {m2.group(2)};'
        # vector<T> -> T* (simplified)
        txt = re.sub(r'\bvector\s*<\s*(\w+)\s*>', r'\1*', txt)
        # map<K,V> -> /* map */ void*
        txt = re.sub(r'\bmap\s*<[^>]+>', '/* map */ void*', txt)
        # unique_ptr/shared_ptr -> raw pointer
        txt = re.sub(r'\bunique_ptr\s*<\s*(\w+)\s*>', r'\1*', txt)
        txt = re.sub(r'\bshared_ptr\s*<\s*(\w+)\s*>', r'\1*', txt)
        # array<T,N> -> T[N]
        txt = re.sub(r'\barray\s*<\s*(\w+)\s*,\s*(\d+)\s*>', r'\1', txt)
        return txt

    def _translate_expr_text(self, txt: str) -> str:
        """Translate C++ expression patterns in arbitrary text."""
        import re

        # true/false -> 1/0
        txt = re.sub(r'\btrue\b', '1', txt)
        txt = re.sub(r'\bfalse\b', '0', txt)

        # nullptr -> NULL
        txt = re.sub(r'\bnullptr\b', 'NULL', txt)

        # new type[size] -> malloc
        txt = re.sub(r'\bnew\s+(\w+)\[([^\]]+)\]',
                      r'(\1*)malloc((\2) * sizeof(\1))', txt)
        txt = re.sub(r'\bnew\s+(\w+)\(\)',
                      r'(\1*)malloc(sizeof(\1))', txt)
        txt = re.sub(r'\bnew\s+(\w+)\(([^)]+)\)',
                      r'(\1*)malloc(sizeof(\1))', txt)

        # delete[] -> free
        txt = re.sub(r'\bdelete\[\]\s*(\w+)', r'free(\1)', txt)
        txt = re.sub(r'\bdelete\s+(\w+)', r'free(\1)', txt)

        # Casts: static_cast<T>(e) -> (T)(e)
        txt = re.sub(r'static_cast<([^>]+)>\(([^)]+)\)', r'(\1)(\2)', txt)
        txt = re.sub(r'dynamic_cast<([^>]+)>\(([^)]+)\)', r'(\1)(\2)', txt)
        txt = re.sub(r'reinterpret_cast<([^>]+)>\(([^)]+)\)', r'(\1)(\2)', txt)
        txt = re.sub(r'const_cast<([^>]+)>\(([^)]+)\)', r'(\1)(\2)', txt)

        # ── C++ string methods -> C string funcs ──
        txt = re.sub(r'(\w+)\.length\(\)', r'strlen(\1)', txt)
        txt = re.sub(r'(\w+)\.size\(\)', r'strlen(\1)', txt)
        txt = re.sub(r'(\w+)\.compare\(([^)]+)\)', r'strcmp(\1, \2)', txt)
        txt = re.sub(r'(\w+)\.find\(([^)]+)\)\s*!=\s*(?:string::)?npos', r'(strstr(\1, \2) != NULL)', txt)
        txt = re.sub(r'(\w+)\.find\(([^)]+)\)', r'strstr(\1, \2)', txt)
        txt = re.sub(r'(\w+)\.rfind\(([^)]+)\)', r'strrchr(\1, \2)', txt)
        txt = re.sub(r'(\w+)\.empty\(\)', r'(strlen(\1) == 0)', txt)
        txt = re.sub(r'(\w+)\.c_str\(\)', r'\1', txt)
        txt = re.sub(r'(\w+)\.substr\(([^)]+)\)', r'(\1 + \2)', txt)
        txt = re.sub(r'(\w+)\.append\(([^)]+)\)', r'strcat(\1, \2)', txt)
        txt = re.sub(r'(\w+)\.push_back\(([^)]+)\)', r'/* push_back \2 */', txt)
        txt = re.sub(r'(\w+)\.pop_back\(\)', r'/* pop_back */', txt)
        txt = re.sub(r'(\w+)\.front\(\)', r'\1[0]', txt)
        txt = re.sub(r'(\w+)\.back\(\)', r'\1[strlen(\1)-1]', txt)
        txt = re.sub(r'(\w+)\.at\((\d+)\)', r'\1[\2]', txt)
        txt = re.sub(r'(\w+)\.clear\(\)', r'\1[0] = 0', txt)
        txt = re.sub(r'(\w+)\.begin\(\)', r'\1', txt)
        txt = re.sub(r'(\w+)\.end\(\)', r'(\1 + strlen(\1))', txt)
        txt = re.sub(r'(\w+)\.erase\(([^)]+)\)', r'/* erase \2 */', txt)
        txt = re.sub(r'(\w+)\.insert\(([^)]+)\)', r'/* insert \2 */', txt)
        txt = re.sub(r'(\w+)\.resize\(([^)]+)\)', r'/* resize \2 */', txt)
        txt = re.sub(r'(\w+)\.reserve\(([^)]+)\)', r'/* reserve \2 */', txt)

        # ── stoi/stod/stol -> atoi/atof/atol ──
        txt = re.sub(r'\bstoi\(', 'atoi(', txt)
        txt = re.sub(r'\bstod\(', 'atof(', txt)
        txt = re.sub(r'\bstol\(', 'atol(', txt)
        txt = re.sub(r'\bstof\(', 'atof(', txt)

        # ── to_string -> sprintf ──
        txt = re.sub(r'\bto_string\(([^)]+)\)', r'/* to_string(\1): use sprintf */', txt)

        # ── sort -> qsort ──
        txt = re.sub(r'\bsort\(([^,]+),\s*([^)]+)\)', r'qsort(\1, (\2) - (\1), sizeof(*(\1)), /* cmp */)', txt)

        # ── swap -> temp variable ──
        txt = re.sub(r'\bswap\(([^,]+),\s*([^)]+)\)', r'{ int _tmp = \1; \1 = \2; \2 = _tmp; }', txt)

        # ── min/max -> ternary ──
        txt = re.sub(r'\bmin\(([^,]+),\s*([^)]+)\)', r'((\1) < (\2) ? (\1) : (\2))', txt)
        txt = re.sub(r'\bmax\(([^,]+),\s*([^)]+)\)', r'((\1) > (\2) ? (\1) : (\2))', txt)

        # ── make_pair -> struct init ──
        txt = re.sub(r'\bmake_pair\(([^,]+),\s*([^)]+)\)', r'{\1, \2}', txt)

        # ── getline -> fgets ──
        txt = re.sub(r'\bgetline\(cin,\s*(\w+)\)', r'fgets(\1, sizeof(\1), stdin)', txt)
        txt = re.sub(r'\bgetline\(([^,]+),\s*(\w+)\)', r'fgets(\2, sizeof(\2), \1)', txt)

        # ── string concatenation: s1 + s2 -> strcat pattern ──
        # Only match when + involves string variables (not arithmetic)
        txt = re.sub(r'(\w+)\s*\+\s*("(?:[^"\\]|\\.)*")', r'/* strcat(\1, \2) */', txt)
        txt = re.sub(r'("(?:[^"\\]|\\.)*")\s*\+\s*(\w+)', r'/* strcat(\1, \2) */', txt)

        # ── this-> -> self-> ──
        txt = re.sub(r'\bthis\s*->', 'self->', txt)
        txt = re.sub(r'\bthis\b', 'self', txt)

        # ── string::npos -> -1 ──
        txt = re.sub(r'string::npos', '(-1)', txt)
        txt = re.sub(r'\bnpos\b', '(-1)', txt)

        # ── std:: removal ──
        txt = re.sub(r'\bstd::', '', txt)

        # ── Lambda: [...](...){...} -> /* lambda */ ──
        txt = re.sub(r'\[([^\]]*)\]\s*\(([^)]*)\)\s*\{([^}]*)\}', r'/* lambda(\2){\3} */', txt)

        return txt


# ---------------------------------------------------------------------------
#  Public API
# ---------------------------------------------------------------------------
def translate_string(cpp_source: str) -> str:
    t = CppToCTranslator()
    return t.translate(cpp_source)


def translate_file(cpp_path: str) -> str:
    with open(cpp_path, encoding='utf-8') as f:
        return translate_string(f.read())
