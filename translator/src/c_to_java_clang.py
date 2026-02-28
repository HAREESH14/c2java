#!/usr/bin/env python3
"""
c_to_java_clang.py  –  Semantic C-to-Java translator using LLVM libclang.

This script must run inside WSL because libclang is installed there.
Usage:  python3 c_to_java_clang.py <input.c>
Output: prints the translated Java code to stdout.

Architecture
------------
Unlike the pycparser-based translator that guesses types from syntax,
this uses Clang's full semantic engine.  Every cursor carries its
resolved type, so we can distinguish:
  char *s (used as String)  vs  char buf[100] (used as char[])
  int returned as pseudo-boolean  vs  real int
"""

import sys, os
import clang.cindex as ci
from clang.cindex import CursorKind as CK, TypeKind as TK

# ── helpers ────────────────────────────────────────────────────────────────

C_TO_JAVA_TYPE = {
    'int': 'int', 'short': 'short', 'long': 'long',
    'long long': 'long', 'unsigned int': 'int', 'unsigned long': 'long',
    'unsigned long long': 'long', 'unsigned short': 'short',
    'unsigned char': 'int', 'signed char': 'char',
    'float': 'float', 'double': 'double', 'long double': 'double',
    'char': 'char', 'void': 'void', '_Bool': 'boolean',
}

MATH_FUNCS = {
    'sqrt': 'Math.sqrt', 'pow': 'Math.pow', 'abs': 'Math.abs',
    'fabs': 'Math.abs', 'sin': 'Math.sin', 'cos': 'Math.cos',
    'tan': 'Math.tan', 'log': 'Math.log', 'log10': 'Math.log10',
    'exp': 'Math.exp', 'ceil': 'Math.ceil', 'floor': 'Math.floor',
    'round': 'Math.round', 'fmax': 'Math.max', 'fmin': 'Math.min',
    'atan2': 'Math.atan2', 'asin': 'Math.asin', 'acos': 'Math.acos',
}

MACRO_CONSTS = {
    'M_PI': 'Math.PI', 'M_E': 'Math.E',
    'INT_MAX': 'Integer.MAX_VALUE', 'INT_MIN': 'Integer.MIN_VALUE',
    'LONG_MAX': 'Long.MAX_VALUE', 'LONG_MIN': 'Long.MIN_VALUE',
}


def _map_type(clang_type_spelling: str) -> str:
    """Map a Clang type spelling to a Java type."""
    s = clang_type_spelling.replace('const ', '').replace('restrict ', '').strip()

    # pointer types
    if s == 'char *' or s == 'const char *':
        return 'String'
    if s.endswith(' *'):
        base = s[:-2].strip()
        jt = C_TO_JAVA_TYPE.get(base, base)
        return f'{jt}[]'

    # 2D arrays like int[2][2]
    if s.count('[') >= 2:
        base = s[:s.index('[')].strip()
        jt = C_TO_JAVA_TYPE.get(base, base)
        return f'{jt}[][]'

    # sized arrays like char[100]
    if '[' in s:
        base = s[:s.index('[')].strip()
        jt = C_TO_JAVA_TYPE.get(base, base)
        return f'{jt}[]'

    return C_TO_JAVA_TYPE.get(s, s)


def _map_type_for_param(cursor) -> str:
    """Map a PARM_DECL cursor to the correct Java type.
    Uses semantic analysis: if a char* is ever indexed in the function body,
    it is a char[] buffer, not a String.
    """
    t = cursor.type.spelling.replace('const ', '').replace('restrict ', '').strip()

    if t in ('char *', 'const char *'):
        # Check if this parameter is used with array subscript in the parent function
        parent = cursor.semantic_parent
        if parent and _is_char_ptr_indexed(parent, cursor.spelling):
            return 'char[]'
        return 'String'

    return _map_type(cursor.type.spelling)


def _is_char_ptr_indexed(func_cursor, var_name: str) -> bool:
    """Walk a function body looking for array subscript access on 'var_name'."""
    for c in func_cursor.walk_preorder():
        if c.kind == CK.ARRAY_SUBSCRIPT_EXPR:
            children = list(c.get_children())
            if children:
                base = children[0]
                # unwrap implicit casts
                while base.kind == CK.UNEXPOSED_EXPR:
                    inner = list(base.get_children())
                    if inner:
                        base = inner[0]
                    else:
                        break
                if base.kind == CK.DECL_REF_EXPR and base.spelling == var_name:
                    return True
    return False


def _get_tokens_str(cursor) -> str:
    """Get the raw source tokens for a cursor."""
    tokens = list(cursor.get_tokens())
    return ' '.join(t.spelling for t in tokens)


def _get_array_size(cursor) -> str:
    """For a VAR_DECL that is an array, extract the size."""
    t = cursor.type.spelling
    if '[' in t:
        start = t.index('[') + 1
        end = t.index(']')
        return t[start:end].strip() or '0'
    return '0'


def _default_value(java_type: str) -> str:
    """Return a sensible default for uninitialized Java primitives."""
    defaults = {
        'int': '0', 'long': '0L', 'short': '0', 'float': '0.0f',
        'double': '0.0', 'char': "'\\0'", 'boolean': 'false', 'byte': '0',
    }
    return defaults.get(java_type, '')


# ── main translator class ─────────────────────────────────────────────────

class ClangToJava:
    def __init__(self, tu):
        self.tu = tu
        self.output = []
        self.indent = 0
        self.structs = []   # collected struct declarations
        self.funcs = []     # collected function declarations (non-main)
        self.main_func = None
        self.is_main = False
        self.func_return_types = {}  # name -> java return type

    def emit(self, line: str):
        self.output.append('    ' * self.indent + line)

    def translate(self) -> str:
        src_file = self.tu.spelling

        # First pass: collect function return types for semantic boolean resolution
        for cursor in self.tu.cursor.get_children():
            if not cursor.location.file:
                continue
            if cursor.location.file.name != src_file:
                continue
            if cursor.kind == CK.FUNCTION_DECL:
                ret = _map_type(cursor.result_type.spelling)
                self.func_return_types[cursor.spelling] = ret

        # Emit header
        self.emit('import java.lang.Math;')
        self.emit('')
        self.emit('public class Main {')
        self.emit('')
        self.indent = 1

        # Second pass: translate top-level declarations
        for cursor in self.tu.cursor.get_children():
            if not cursor.location.file:
                continue
            if cursor.location.file.name != src_file:
                continue
            self._visit_top(cursor)

        self.indent = 0
        self.emit('')
        self.emit('}')
        return '\n'.join(self.output)

    def _visit_top(self, cursor):
        if cursor.kind == CK.STRUCT_DECL:
            self._struct(cursor)
        elif cursor.kind == CK.ENUM_DECL:
            self._enum(cursor)
        elif cursor.kind == CK.FUNCTION_DECL:
            self._function(cursor)
        elif cursor.kind == CK.VAR_DECL:
            self._global_var(cursor)
        elif cursor.kind == CK.TYPEDEF_DECL:
            pass  # typedefs are resolved by Clang automatically

    # ── struct ─────────────────────────────────────────────────────────────

    def _struct(self, cursor):
        name = cursor.spelling
        self.emit(f'static class {name} {{')
        self.indent += 1
        for field in cursor.get_children():
            if field.kind == CK.FIELD_DECL:
                jt = _map_type(field.type.spelling)
                self.emit(f'{jt} {field.spelling};')
        self.indent -= 1
        self.emit('}')
        self.emit('')

    # ── enum ───────────────────────────────────────────────────────────────

    def _enum(self, cursor):
        name = cursor.spelling or 'AnonymousEnum'
        vals = []
        for c in cursor.get_children():
            if c.kind == CK.ENUM_CONSTANT_DECL:
                vals.append(c.spelling)
        self.emit(f'// enum {name}')
        for i, v in enumerate(vals):
            self.emit(f'public static final int {v} = {i};')
        self.emit('')

    # ── function ───────────────────────────────────────────────────────────

    def _function(self, cursor):
        name = cursor.spelling
        ret_type = _map_type(cursor.result_type.spelling)

        self.is_main = (name == 'main')

        # Build parameter list with semantic type resolution
        params = []
        for child in cursor.get_children():
            if child.kind == CK.PARM_DECL:
                ptype = _map_type_for_param(child)
                pname = child.spelling or f'arg{len(params)}'
                params.append(f'{ptype} {pname}')

        if self.is_main:
            self.emit('public static void main(String[] args) {')
        else:
            param_str = ', '.join(params)
            self.emit(f'public static {ret_type} {name}({param_str}) {{')

        self.indent += 1

        # Find the compound statement (function body)
        for child in cursor.get_children():
            if child.kind == CK.COMPOUND_STMT:
                self._compound(child)
                break

        self.indent -= 1
        self.emit('}')
        self.emit('')
        self.is_main = False

    # ── global variable ────────────────────────────────────────────────────

    def _global_var(self, cursor):
        jt = _map_type(cursor.type.spelling)
        name = cursor.spelling
        children = list(cursor.get_children())
        if children:
            init = self._expr(children[-1])
            self.emit(f'static {jt} {name} = {init};')
        else:
            self.emit(f'static {jt} {name};')

    # ── compound / block ───────────────────────────────────────────────────

    def _compound(self, cursor):
        for child in cursor.get_children():
            self._stmt(child)

    # ── statement dispatcher ───────────────────────────────────────────────

    def _stmt(self, cursor):
        k = cursor.kind

        if k == CK.DECL_STMT:
            for child in cursor.get_children():
                self._local_var(child)

        elif k == CK.RETURN_STMT:
            self._return(cursor)

        elif k == CK.IF_STMT:
            self._if(cursor)

        elif k == CK.FOR_STMT:
            self._for(cursor)

        elif k == CK.WHILE_STMT:
            self._while(cursor)

        elif k == CK.DO_STMT:
            self._dowhile(cursor)

        elif k == CK.SWITCH_STMT:
            self._switch(cursor)

        elif k == CK.COMPOUND_STMT:
            self.emit('{')
            self.indent += 1
            self._compound(cursor)
            self.indent -= 1
            self.emit('}')

        elif k == CK.BREAK_STMT:
            self.emit('break;')

        elif k == CK.CONTINUE_STMT:
            self.emit('continue;')

        elif k == CK.NULL_STMT:
            self.emit(';')

        elif k == CK.CALL_EXPR:
            self.emit(f'{self._expr(cursor)};')

        elif k in (CK.BINARY_OPERATOR, CK.COMPOUND_ASSIGNMENT_OPERATOR,
                    CK.UNARY_OPERATOR):
            self.emit(f'{self._expr(cursor)};')

        else:
            # Fallback: try to emit as expression statement
            expr = self._expr(cursor)
            if expr and expr != '/* ? */':
                self.emit(f'{expr};')

    # ── local variable declaration ─────────────────────────────────────────

    def _local_var(self, cursor):
        if cursor.kind != CK.VAR_DECL:
            return
        name = cursor.spelling
        raw_type = cursor.type.spelling.replace('const ', '').replace('restrict ', '').strip()
        children = list(cursor.get_children())

        is_const = 'const' in (cursor.type.spelling or '')
        prefix = 'final ' if is_const else ''

        # Semantic: struct type -> instantiate with new
        if cursor.type.kind == TK.RECORD:
            struct_name = cursor.type.spelling.replace('struct ', '')
            self.emit(f'{prefix}{struct_name} {name} = new {struct_name}();')
            return

        # Semantic: char[N] -> char array; char * with string init -> String
        if raw_type.startswith('char') and '[' in raw_type:
            size = _get_array_size(cursor)
            if children and children[-1].kind == CK.STRING_LITERAL:
                init = self._expr(children[-1])
                # Check if this char[] is indexed later -> use toCharArray()
                parent = cursor.semantic_parent
                if parent and _is_char_ptr_indexed(parent, name):
                    self.emit(f'{prefix}char[] {name} = {init}.toCharArray();')
                else:
                    self.emit(f'{prefix}String {name} = {init};')
            else:
                self.emit(f'{prefix}char[] {name} = new char[{size}];')
            return

        if raw_type in ('char *', 'const char *'):
            # Semantic: check if this char* is indexed later
            parent = cursor.semantic_parent
            is_indexed = parent and _is_char_ptr_indexed(parent, name)
            if children:
                init = self._expr(children[-1])
                if is_indexed:
                    # char *buf = malloc(...) but indexed -> char[]
                    if 'new ' in init:
                        # Force char array type regardless of what malloc returned
                        import re
                        init = re.sub(r'new \w+\[', 'new char[', init)
                        self.emit(f'{prefix}char[] {name} = {init};')
                    else:
                        self.emit(f'{prefix}char[] {name} = {init}.toCharArray();')
                else:
                    self.emit(f'{prefix}String {name} = {init};')
            else:
                if is_indexed:
                    self.emit(f'{prefix}char[] {name} = null;')
                else:
                    self.emit(f'{prefix}String {name} = null;')
            return

        jt = _map_type(raw_type)

        # Pointer -> array
        if raw_type.endswith(' *'):
            if children:
                init = self._expr(children[-1])
                self.emit(f'{prefix}{jt} {name} = {init};')
            else:
                self.emit(f'{prefix}{jt} {name} = null;')
            return

        # 2D Array types int[N][M]
        if raw_type.count('[') >= 2:
            base = raw_type[:raw_type.index('[')].strip()
            jbase = C_TO_JAVA_TYPE.get(base, base)
            # Extract both dimensions
            dims = []
            tmp = raw_type
            while '[' in tmp:
                s_idx = tmp.index('[') + 1
                e_idx = tmp.index(']')
                dims.append(tmp[s_idx:e_idx].strip() or '0')
                tmp = tmp[e_idx+1:]
            if children:
                last = children[-1]
                if last.kind == CK.INIT_LIST_EXPR:
                    init = self._expr(last)
                    self.emit(f'{prefix}{jbase}[][] {name} = {init};')
                else:
                    d0 = dims[0] if len(dims) > 0 else '0'
                    d1 = dims[1] if len(dims) > 1 else '0'
                    self.emit(f'{prefix}{jbase}[][] {name} = new {jbase}[{d0}][{d1}];')
            else:
                d0 = dims[0] if len(dims) > 0 else '0'
                d1 = dims[1] if len(dims) > 1 else '0'
                self.emit(f'{prefix}{jbase}[][] {name} = new {jbase}[{d0}][{d1}];')
            return

        # 1D Array types
        if '[' in raw_type:
            size = _get_array_size(cursor)
            base = raw_type[:raw_type.index('[')].strip()
            jbase = C_TO_JAVA_TYPE.get(base, base)
            if children:
                last = children[-1]
                if last.kind == CK.INIT_LIST_EXPR:
                    init = self._expr(last)
                    self.emit(f'{prefix}{jbase}[] {name} = {init};')
                else:
                    self.emit(f'{prefix}{jbase}[] {name} = new {jbase}[{size}];')
            else:
                self.emit(f'{prefix}{jbase}[] {name} = new {jbase}[{size}];')
            return

        # Normal variable
        if children:
            # Skip TYPE_REF children, get actual initializer
            init_child = None
            for ch in children:
                if ch.kind != CK.TYPE_REF:
                    init_child = ch
            if init_child:
                init = self._expr(init_child)
                self.emit(f'{prefix}{jt} {name} = {init};')
            else:
                # Uninitialized: add default for primitives
                default = _default_value(jt)
                if default:
                    self.emit(f'{prefix}{jt} {name} = {default};')
                else:
                    self.emit(f'{prefix}{jt} {name};')
        else:
            # Uninitialized: add default for primitives
            default = _default_value(jt)
            if default:
                self.emit(f'{prefix}{jt} {name} = {default};')
            else:
                self.emit(f'{prefix}{jt} {name};')

    # ── return ─────────────────────────────────────────────────────────────

    def _return(self, cursor):
        children = list(cursor.get_children())
        if not children:
            self.emit('return;')
            return
        val = self._expr(children[0])
        if self.is_main:
            if val == '0':
                self.emit('return;')
            else:
                self.emit(f'System.exit({val});')
                self.emit('return;')
        else:
            # Check if returning a boolean expression from an int function
            child = children[0]
            # Unwrap implicit casts
            while child.kind == CK.UNEXPOSED_EXPR:
                inner = list(child.get_children())
                if inner:
                    child = inner[0]
                else:
                    break
            if child.kind == CK.BINARY_OPERATOR:
                op = _get_binary_op(child)
                if op in ('==', '!=', '<', '>', '<=', '>='):
                    # Boolean expr in non-boolean function
                    self.emit(f'return ({val}) ? 1 : 0;')
                    return
            self.emit(f'return {val};')

    # ── if ─────────────────────────────────────────────────────────────────

    def _if(self, cursor):
        children = list(cursor.get_children())
        if len(children) < 2:
            return
        cond = self._bool_expr(children[0])
        self.emit(f'if ({cond}) {{')
        self.indent += 1
        self._stmt(children[1])
        self.indent -= 1
        if len(children) >= 3:
            # else branch
            else_branch = children[2]
            if else_branch.kind == CK.IF_STMT:
                # else if
                inner_children = list(else_branch.get_children())
                if len(inner_children) >= 2:
                    cond2 = self._bool_expr(inner_children[0])
                    self.emit(f'}} else if ({cond2}) {{')
                    self.indent += 1
                    self._stmt(inner_children[1])
                    self.indent -= 1
                    if len(inner_children) >= 3:
                        self.emit('} else {')
                        self.indent += 1
                        self._stmt(inner_children[2])
                        self.indent -= 1
            else:
                self.emit('} else {')
                self.indent += 1
                self._stmt(else_branch)
                self.indent -= 1
        self.emit('}')

    # ── for ────────────────────────────────────────────────────────────────

    def _for(self, cursor):
        children = list(cursor.get_children())
        # Clang FOR_STMT children: [init, cond, incr, body]
        # But some may be NULL_STMT if omitted
        parts = []
        body = None
        for ch in children:
            if ch.kind == CK.COMPOUND_STMT or (ch.kind not in (
                CK.DECL_STMT, CK.BINARY_OPERATOR, CK.COMPOUND_ASSIGNMENT_OPERATOR,
                CK.UNARY_OPERATOR, CK.NULL_STMT, CK.CALL_EXPR,
                CK.UNEXPOSED_EXPR, CK.PAREN_EXPR, CK.DECL_REF_EXPR,
                CK.INTEGER_LITERAL
            ) and ch.kind not in (CK.BINARY_OPERATOR, CK.COMPOUND_ASSIGNMENT_OPERATOR)):
                if ch.kind == CK.COMPOUND_STMT:
                    body = ch
                elif ch.kind in (CK.IF_STMT, CK.RETURN_STMT, CK.CALL_EXPR,
                                 CK.BREAK_STMT, CK.CONTINUE_STMT, CK.FOR_STMT,
                                 CK.WHILE_STMT):
                    body = ch

        # Use token-based approach for the for-header
        tokens = list(cursor.get_tokens())
        # Find everything between 'for' '(' ... ')' '{'
        header = _get_tokens_str(cursor)

        # Simpler: extract for(...) from tokens
        init_s, cond_s, incr_s = '', '', ''

        # Parse children semantically
        idx = 0
        child_list = list(cursor.get_children())
        body_node = child_list[-1] if child_list else None

        # The non-body children represent init, cond, incr
        non_body = child_list[:-1] if len(child_list) > 1 else []

        for i, ch in enumerate(non_body):
            if i == 0:
                # init
                if ch.kind == CK.DECL_STMT:
                    inner = list(ch.get_children())
                    if inner and inner[0].kind == CK.VAR_DECL:
                        v = inner[0]
                        jt = _map_type(v.type.spelling)
                        vinit = list(v.get_children())
                        if vinit:
                            init_val = self._expr(vinit[-1])
                            init_s = f'{jt} {v.spelling} = {init_val}'
                        else:
                            init_s = f'{jt} {v.spelling} = 0'
                elif ch.kind == CK.NULL_STMT:
                    init_s = ''
                else:
                    init_s = self._expr(ch)
            elif i == 1:
                # condition
                if ch.kind == CK.NULL_STMT:
                    cond_s = ''
                else:
                    cond_s = self._expr(ch)
            elif i == 2:
                # increment
                if ch.kind == CK.NULL_STMT:
                    incr_s = ''
                else:
                    incr_s = self._expr(ch)

        self.emit(f'for ({init_s}; {cond_s}; {incr_s}) {{')
        self.indent += 1
        if body_node:
            if body_node.kind == CK.COMPOUND_STMT:
                self._compound(body_node)
            else:
                self._stmt(body_node)
        self.indent -= 1
        self.emit('}')

    # ── while ──────────────────────────────────────────────────────────────

    def _while(self, cursor):
        children = list(cursor.get_children())
        if len(children) < 2:
            return
        cond = self._bool_expr(children[0])
        self.emit(f'while ({cond}) {{')
        self.indent += 1
        if children[1].kind == CK.COMPOUND_STMT:
            self._compound(children[1])
        else:
            self._stmt(children[1])
        self.indent -= 1
        self.emit('}')

    # ── do-while ───────────────────────────────────────────────────────────

    def _dowhile(self, cursor):
        children = list(cursor.get_children())
        if len(children) < 2:
            return
        self.emit('do {')
        self.indent += 1
        if children[0].kind == CK.COMPOUND_STMT:
            self._compound(children[0])
        else:
            self._stmt(children[0])
        self.indent -= 1
        cond = self._bool_expr(children[1])
        self.emit(f'}} while ({cond});')

    # ── switch ─────────────────────────────────────────────────────────────

    def _switch(self, cursor):
        children = list(cursor.get_children())
        if not children:
            return
        cond = self._expr(children[0])
        self.emit(f'switch ({cond}) {{')
        self.indent += 1
        if len(children) > 1:
            body = children[1]
            if body.kind == CK.COMPOUND_STMT:
                for ch in body.get_children():
                    if ch.kind == CK.CASE_STMT:
                        self._case(ch)
                    elif ch.kind == CK.DEFAULT_STMT:
                        self._default(ch)
                    else:
                        self._stmt(ch)
        self.indent -= 1
        self.emit('}')

    def _case(self, cursor):
        children = list(cursor.get_children())
        if children:
            val = self._expr(children[0])
            self.emit(f'case {val}:')
            self.indent += 1
            for ch in children[1:]:
                self._stmt(ch)
            self.indent -= 1

    def _default(self, cursor):
        self.emit('default:')
        self.indent += 1
        for ch in cursor.get_children():
            self._stmt(ch)
        self.indent -= 1

    # ── boolean expression wrapper ─────────────────────────────────────────

    def _bool_expr(self, cursor) -> str:
        """Wrap an expression for Java boolean context.
        If the expression type is int (not already boolean), append != 0."""
        expr_str = self._expr(cursor)

        # unwrap implicit casts to find the real expression
        real = cursor
        while real.kind == CK.UNEXPOSED_EXPR:
            inner = list(real.get_children())
            if inner:
                real = inner[0]
            else:
                break

        # If it's already a comparison operator, it's boolean
        if real.kind == CK.BINARY_OPERATOR:
            op = _get_binary_op(real)
            if op in ('==', '!=', '<', '>', '<=', '>=', '&&', '||'):
                return expr_str

        if real.kind == CK.UNARY_OPERATOR:
            tok = list(real.get_tokens())
            if tok and tok[0].spelling == '!':
                return expr_str

        # If it's a PAREN_EXPR, check inside
        if real.kind == CK.PAREN_EXPR:
            inner = list(real.get_children())
            if inner:
                return self._bool_expr(inner[0])

        # Check the result type: if it's int/long, wrap with != 0
        type_kind = cursor.type.kind
        if type_kind in (TK.INT, TK.LONG, TK.LONGLONG, TK.SHORT,
                         TK.UINT, TK.ULONG, TK.ULONGLONG, TK.USHORT,
                         TK.SCHAR, TK.UCHAR, TK.CHAR_S, TK.CHAR_U):
            return f'({expr_str}) != 0'

        return expr_str

    # ── expression emitter ─────────────────────────────────────────────────

    def _expr(self, cursor) -> str:
        k = cursor.kind

        if k == CK.INTEGER_LITERAL:
            tokens = list(cursor.get_tokens())
            return tokens[0].spelling if tokens else '0'

        if k == CK.FLOATING_LITERAL:
            tokens = list(cursor.get_tokens())
            return tokens[0].spelling if tokens else '0.0'

        if k == CK.CHARACTER_LITERAL:
            tokens = list(cursor.get_tokens())
            return tokens[0].spelling if tokens else "'?'"

        if k == CK.STRING_LITERAL:
            tokens = list(cursor.get_tokens())
            return tokens[0].spelling if tokens else '""'

        if k == CK.DECL_REF_EXPR:
            name = cursor.spelling
            return MACRO_CONSTS.get(name, name)

        if k == CK.UNEXPOSED_EXPR:
            children = list(cursor.get_children())
            if children:
                return self._expr(children[0])
            tokens = list(cursor.get_tokens())
            return tokens[0].spelling if tokens else '/* ? */'

        if k == CK.PAREN_EXPR:
            children = list(cursor.get_children())
            if children:
                return f'({self._expr(children[0])})'
            return '()'

        if k == CK.BINARY_OPERATOR:
            children = list(cursor.get_children())
            if len(children) == 2:
                lhs = self._expr(children[0])
                rhs = self._expr(children[1])
                op = _get_binary_op(cursor)
                return f'{lhs} {op} {rhs}'

        if k == CK.COMPOUND_ASSIGNMENT_OPERATOR:
            children = list(cursor.get_children())
            if len(children) == 2:
                lhs = self._expr(children[0])
                rhs = self._expr(children[1])
                op = _get_compound_assign_op(cursor)
                return f'{lhs} {op} {rhs}'

        if k == CK.UNARY_OPERATOR:
            return self._unary(cursor)

        if k == CK.CALL_EXPR:
            return self._call(cursor)

        if k == CK.ARRAY_SUBSCRIPT_EXPR:
            children = list(cursor.get_children())
            if len(children) == 2:
                arr = self._expr(children[0])
                idx = self._expr(children[1])
                return f'{arr}[{idx}]'

        if k == CK.MEMBER_REF_EXPR:
            children = list(cursor.get_children())
            field = cursor.spelling
            if children:
                obj = self._expr(children[0])
                return f'{obj}.{field}'
            return field

        if k == CK.INIT_LIST_EXPR:
            children = list(cursor.get_children())
            items = ', '.join(self._expr(c) for c in children)
            return '{' + items + '}'

        if k == CK.CONDITIONAL_OPERATOR:
            children = list(cursor.get_children())
            if len(children) == 3:
                cond = self._bool_expr(children[0])
                t = self._expr(children[1])
                f = self._expr(children[2])
                return f'({cond} ? {t} : {f})'

        if k == CK.CSTYLE_CAST_EXPR:
            children = list(cursor.get_children())
            if children:
                inner = self._expr(children[-1])
                # Skip casts to malloc results (they become new)
                if inner.startswith('new '):
                    return inner
                cast_type = _map_type(cursor.type.spelling)
                return f'({cast_type}){inner}'

        if k == CK.CXX_UNARY_EXPR:
            # sizeof
            tokens = list(cursor.get_tokens())
            return '4'  # sizeof approximation

        if k == CK.NULL_STMT:
            return ''

        # Fallback: try token reconstruction
        tokens = list(cursor.get_tokens())
        if tokens:
            return ' '.join(t.spelling for t in tokens)
        return '/* ? */'

    # ── unary operator ─────────────────────────────────────────────────────

    def _unary(self, cursor):
        children = list(cursor.get_children())
        tokens = list(cursor.get_tokens())

        if not children:
            return _get_tokens_str(cursor)

        child_expr = self._expr(children[0])

        if not tokens:
            return child_expr

        first_tok = tokens[0].spelling
        last_tok = tokens[-1].spelling

        # Prefix operators
        if first_tok in ('-', '+', '~', '!'):
            return f'{first_tok}{child_expr}'

        # Dereference
        if first_tok == '*':
            # *p -> p[0] for Java
            return f'{child_expr}[0]'

        # Address-of (no direct Java equivalent)
        if first_tok == '&':
            return child_expr

        # Prefix ++/--
        if first_tok in ('++', '--'):
            return f'{first_tok}{child_expr}'

        # Postfix ++/--
        if last_tok in ('++', '--'):
            return f'{child_expr}{last_tok}'

        return child_expr

    # ── function call ──────────────────────────────────────────────────────

    def _call(self, cursor):
        children = list(cursor.get_children())
        if not children:
            return '/* empty call */'

        func_ref = children[0]
        args = [self._expr(c) for c in children[1:]]

        # Get function name
        name = ''
        ref = func_ref
        while ref.kind == CK.UNEXPOSED_EXPR:
            inner = list(ref.get_children())
            if inner:
                ref = inner[0]
            else:
                break
        if ref.kind == CK.DECL_REF_EXPR:
            name = ref.spelling

        # ── Standard library mappings ──

        # printf
        if name in ('printf', 'fprintf'):
            if name == 'fprintf':
                args = args[1:]  # drop FILE* arg
            if args:
                fmt = args[0].replace('\\n', '%n')
                rest = args[1:]
                if rest:
                    return f'System.out.printf({fmt}, {", ".join(rest)})'
                return f'System.out.printf({fmt})'

        # puts
        if name == 'puts':
            return f'System.out.println({", ".join(args)})'

        # putchar
        if name == 'putchar':
            return f'System.out.print((char){args[0]})'

        # scanf → comment
        if name == 'scanf':
            return f'/* scanf({", ".join(args)}) */'

        # malloc/calloc
        if name in ('malloc', 'calloc'):
            # Try to infer the type from the parent cast expression
            # or from the cursor's parent VAR_DECL type
            ret_type = cursor.type.spelling.replace('const ', '').strip()
            if ret_type.endswith(' *'):
                base = ret_type[:-2].strip()
                if base == 'void':
                    base = 'int'  # default: untyped malloc -> int[]
                jt = C_TO_JAVA_TYPE.get(base, base)
            else:
                jt = 'int'
            size = args[0] if args else '10'
            return f'new {jt}[{size}]'

        # free
        if name == 'free':
            return f'/* free({", ".join(args)}) -- Java has GC */'

        # strlen
        if name == 'strlen':
            return f'{args[0]}.length'

        # tolower / toupper
        if name == 'tolower':
            return f'Character.toLowerCase({args[0]})'
        if name == 'toupper':
            return f'Character.toUpperCase({args[0]})'

        # strcmp
        if name == 'strcmp':
            return f'{args[0]}.compareTo({args[1]})'

        # strcpy
        if name == 'strcpy':
            return f'{args[0]} = {args[1]}'

        # strcat
        if name == 'strcat':
            return f'{args[0]} += {args[1]}'

        # sprintf
        if name in ('sprintf', 'snprintf'):
            return f'String.format({", ".join(args[1:])})'

        # memset → Arrays.fill
        if name == 'memset':
            return f'java.util.Arrays.fill({args[0]}, (char){args[1]})'

        # exit
        if name == 'exit':
            return f'System.exit({args[0]})'

        # rand
        if name == 'rand':
            return '(int)(Math.random() * Integer.MAX_VALUE)'

        # srand
        if name == 'srand':
            return f'/* srand({args[0]}) */'

        # atoi
        if name == 'atoi':
            return f'Integer.parseInt({args[0]})'

        # atof
        if name == 'atof':
            return f'Double.parseDouble({args[0]})'

        # Math functions
        if name in MATH_FUNCS:
            return f'{MATH_FUNCS[name]}({", ".join(args)})'

        # Default call
        return f'{name}({", ".join(args)})'


# ── operator extraction helpers ────────────────────────────────────────────

def _get_binary_op(cursor) -> str:
    """Extract the operator string from a BINARY_OPERATOR cursor."""
    children = list(cursor.get_children())
    if len(children) != 2:
        return '?'
    # The operator is the token between the two child spans
    tokens = list(cursor.get_tokens())
    # Collect all tokens from the first child
    lhs_end = children[0].extent.end
    rhs_start = children[1].extent.start
    for tok in tokens:
        loc = tok.extent.start
        if (loc.line > lhs_end.line or
            (loc.line == lhs_end.line and loc.column >= lhs_end.column)):
            if (loc.line < rhs_start.line or
                (loc.line == rhs_start.line and loc.column < rhs_start.column)):
                return tok.spelling
    # Fallback
    all_toks = [t.spelling for t in tokens]
    ops = ['+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=',
           '&&', '||', '&', '|', '^', '<<', '>>', '=']
    for op in ops:
        if op in all_toks:
            idx = all_toks.index(op)
            if idx > 0:
                return op
    return '?'


def _get_compound_assign_op(cursor) -> str:
    """Extract compound assignment operator like +=, -= etc."""
    tokens = list(cursor.get_tokens())
    ops = ['+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=']
    for tok in tokens:
        if tok.spelling in ops:
            return tok.spelling
    return '+='


# ── entry points ───────────────────────────────────────────────────────────

def translate_file(filepath: str) -> str:
    """Translate a C file to Java using libclang."""
    index = ci.Index.create()
    tu = index.parse(filepath, args=['-std=c11'])
    translator = ClangToJava(tu)
    return translator.translate()


def translate_string(source: str) -> str:
    """Translate C source code string to Java."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.c', mode='w',
                                     delete=False, dir='/tmp') as f:
        f.write(source)
        tmp = f.name
    result = translate_file(tmp)
    os.unlink(tmp)
    return result


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 c_to_java_clang.py <input.c>", file=sys.stderr)
        sys.exit(1)
    filepath = sys.argv[1]
    if not os.path.isfile(filepath):
        print(f"Error: file not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    print(translate_file(filepath))
