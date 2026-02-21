# ─────────────────────────────────────────────────────────────────────────────
#  java_to_c_visitor.py
#
#  JavaToCVisitor — walks the Java AST and builds pycparser C AST nodes.
#  Then uses pycparser's CGenerator to emit valid C code.
#
#  *** EXTERNAL LIBRARY USED: pycparser ***
#  pycparser provides:
#    - c_ast.*   : C AST node classes  (Decl, For, If, FuncCall, etc.)
#    - c_generator.CGenerator : walks C AST → emits C source text
#
#  Translation Rules (Java → C):
#    R1  public class Main { }           → (stripped — C has no classes)
#    R2  public static int add(int a)    → int add(int a)
#    R3  public static void main(String[] args) → int main()
#    R4  int x = 5;                      → int x = 5;
#    R5  int[] arr = new int[5];         → int arr[5];
#    R6  int[] arr = {1,2,3};           → int arr[] = {1,2,3};
#    R7  int[][] m = new int[3][3];      → int m[3][3];
#    R8  arr[i]                          → arr[i]
#    R9  m[i][j]                         → m[i][j]
#    R10 x = expr;                       → x = expr;
#    R11 arr[i] = expr;                  → arr[i] = expr;
#    R12 m[i][j] = expr;                 → m[i][j] = expr;
#    R13 if/else if/else                 → if/else if/else
#    R14 for loop                        → for loop
#    R15 while loop                      → while loop
#    R16 do-while                        → do-while
#    R17 System.out.println(x)           → printf("%d\n", x)
#    R17 System.out.printf(fmt, args)    → printf(fmt, args) with %n→\n
#    R18 return expr;                    → return expr;
#    R19 methodCall(args)                → funcCall(args)
#    R20 HashMap<K,V> map = new HashMap<>() → struct + arrays simulation
#    R21 map.put(k, v)                   → hashmap_put(map, k, v)
#    R22 map.get(k)                      → hashmap_get(map, k)
#    R23 All operators                   → same operators
# ─────────────────────────────────────────────────────────────────────────────

from pycparser import c_ast, c_generator
from java_ast_nodes import *


class JavaToCVisitor:

    def __init__(self):
        self.gen          = c_generator.CGenerator()
        self.has_printf   = False    # track if we need #include <stdio.h>
        self.has_hashmap  = False    # track if we need hashmap helpers
        self.func_decls   = []       # forward declarations
        self.hashmap_maps = {}       # map_name → (key_type, val_type)

    def visit(self, node):
        method = 'visit_' + type(node).__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise NotImplementedError(f'No visitor for {type(node).__name__}')

    # ── Emit expression as string (using pycparser CGenerator) ───────────────
    def expr_str(self, node):
        c_node = self.build_expr(node)
        return self.gen.visit(c_node)

    # ── Emit statement as string ──────────────────────────────────────────────
    def stmt_str(self, node):
        c_node = self.build_stmt(node)
        return self.gen.visit(c_node)

    # ═══════════════════════════════════════════════════════════════════════════
    #  R1 — Program
    #  public class Main { } → #include <stdio.h> \n functions...
    # ═══════════════════════════════════════════════════════════════════════════
    def visit_JProgramNode(self, node):
        # Collect all function bodies
        func_bodies = []
        for method in node.methods:
            func_bodies.append(self.visit(method))

        # Build final C output
        lines = []

        # Headers
        lines.append('#include <stdio.h>')
        lines.append('#include <stdlib.h>')
        if self.has_hashmap:
            lines.append('#include <string.h>')

        # HashMap struct definition if needed
        if self.has_hashmap:
            lines.append(self._hashmap_struct_code())

        lines.append('')

        # Forward declarations (for functions defined after main)
        for fd in self.func_decls:
            lines.append(fd)
        if self.func_decls:
            lines.append('')

        # Function bodies
        for fb in func_bodies:
            lines.append(fb)
            lines.append('')

        return '\n'.join(lines)

    # ═══════════════════════════════════════════════════════════════════════════
    #  R2/R3 — Method → C function
    #  public static int add(int a, int b) → int add(int a, int b)
    #  public static void main(String[] args) → int main()
    # ═══════════════════════════════════════════════════════════════════════════
    def visit_JMethodNode(self, node):
        ret_type = 'int' if node.is_main else self.translate_type(node.return_type)

        # Build parameter declarations
        params = []
        if node.is_main:
            pass  # C main() takes no args in our basic version
        else:
            for p in node.params:
                if p.type_ == 'void': continue
                if p.is_array:
                    # int arr[]  →  int arr[]
                    arr_decl = c_ast.ArrayDecl(
                        type=c_ast.TypeDecl(p.name, [], None,
                                            c_ast.IdentifierType([p.type_])),
                        dim=None,
                        dim_quals=[]
                    )
                    params.append(c_ast.Decl(
                        name=p.name, quals=[], align=[], storage=[], funcspec=[],
                        type=arr_decl, init=None, bitsize=None
                    ))
                else:
                    params.append(c_ast.Decl(
                        name=p.name, quals=[], align=[], storage=[], funcspec=[],
                        type=c_ast.TypeDecl(p.name, [], None,
                                           c_ast.IdentifierType([p.type_])),
                        init=None, bitsize=None
                    ))

        param_list = c_ast.ParamList(params) if params else None

        # Build body statements
        body_stmts = []
        for stmt in node.body.statements:
            c_stmt = self.build_stmt(stmt)
            if c_stmt is not None:
                body_stmts.append(c_stmt)

        # Add return 0 to main
        if node.is_main:
            body_stmts.append(c_ast.Return(c_ast.Constant('int', '0')))

        compound = c_ast.Compound(body_stmts)

        # Build function declaration
        func_decl = c_ast.FuncDecl(
            args=param_list,
            type=c_ast.TypeDecl(node.name, [], None,
                                c_ast.IdentifierType([ret_type]))
        )
        decl = c_ast.Decl(
            name=node.name, quals=[], align=[], storage=[], funcspec=[],
            type=func_decl, init=None, bitsize=None
        )
        func_def = c_ast.FuncDef(decl=decl, param_decls=None, body=compound)
        return self.gen.visit(func_def)

    # ═══════════════════════════════════════════════════════════════════════════
    #  Build a C AST statement node from a Java AST statement node
    # ═══════════════════════════════════════════════════════════════════════════
    def build_stmt(self, node):

        # ── R4 — Variable declaration ─────────────────────────────────────────
        if isinstance(node, JVarDeclNode):
            c_type = self.translate_type(node.type_)
            init   = self.build_expr(node.initializer) if node.initializer else None
            return c_ast.Decl(
                name=node.name, quals=[], align=[], storage=[], funcspec=[],
                type=c_ast.TypeDecl(node.name, [], None,
                                    c_ast.IdentifierType([c_type])),
                init=init, bitsize=None
            )

        # ── R5/R6 — 1D Array declaration ─────────────────────────────────────
        if isinstance(node, JArrayDeclNode):
            c_type = self.translate_type(node.type_)
            if node.init_values:
                # int arr[] = {1,2,3}
                vals = [self.build_expr(v) for v in node.init_values]
                init = c_ast.NamedInitializer(name=None,
                           expr=c_ast.ExprList(vals)) if len(vals) > 1 else None
                # Use compound literal approach
                init_list = c_ast.InitList(exprs=vals)
                arr_type  = c_ast.ArrayDecl(
                    type=c_ast.TypeDecl(node.name, [], None,
                                        c_ast.IdentifierType([c_type])),
                    dim=None, dim_quals=[]
                )
                return c_ast.Decl(
                    name=node.name, quals=[], align=[], storage=[], funcspec=[],
                    type=arr_type, init=init_list, bitsize=None
                )
            else:
                # int arr[5]  OR  int arr[] = new int[size]
                size_expr = self.build_expr(node.size) if node.size else None
                arr_type  = c_ast.ArrayDecl(
                    type=c_ast.TypeDecl(node.name, [], None,
                                        c_ast.IdentifierType([c_type])),
                    dim=size_expr, dim_quals=[]
                )
                return c_ast.Decl(
                    name=node.name, quals=[], align=[], storage=[], funcspec=[],
                    type=arr_type, init=None, bitsize=None
                )

        # ── R7 — 2D Array declaration ─────────────────────────────────────────
        if isinstance(node, JArray2DDeclNode):
            c_type   = self.translate_type(node.type_)
            cols_e   = self.build_expr(node.cols)
            rows_e   = self.build_expr(node.rows)
            inner    = c_ast.ArrayDecl(
                type=c_ast.TypeDecl(node.name, [], None,
                                    c_ast.IdentifierType([c_type])),
                dim=cols_e, dim_quals=[]
            )
            outer    = c_ast.ArrayDecl(type=inner, dim=rows_e, dim_quals=[])
            return c_ast.Decl(
                name=node.name, quals=[], align=[], storage=[], funcspec=[],
                type=outer, init=None, bitsize=None
            )

        # ── R10 — Simple assignment ────────────────────────────────────────────
        if isinstance(node, JAssignNode):
            return c_ast.Assignment(
                op='=',
                lvalue=c_ast.ID(node.name),
                rvalue=self.build_expr(node.value)
            )

        # ── R11 — Array assignment ─────────────────────────────────────────────
        if isinstance(node, JArrayAssignNode):
            return c_ast.Assignment(
                op='=',
                lvalue=c_ast.ArrayRef(
                    name=c_ast.ID(node.name),
                    subscript=self.build_expr(node.index)
                ),
                rvalue=self.build_expr(node.value)
            )

        # ── R12 — 2D Array assignment ──────────────────────────────────────────
        if isinstance(node, JArray2DAssignNode):
            inner_ref = c_ast.ArrayRef(
                name=c_ast.ID(node.name),
                subscript=self.build_expr(node.row)
            )
            return c_ast.Assignment(
                op='=',
                lvalue=c_ast.ArrayRef(name=inner_ref,
                                      subscript=self.build_expr(node.col)),
                rvalue=self.build_expr(node.value)
            )

        # ── R13 — if/else ─────────────────────────────────────────────────────
        if isinstance(node, JIfNode):
            return self._build_if(node)

        # ── R14 — for loop ────────────────────────────────────────────────────
        if isinstance(node, JForNode):
            init_s   = self.build_stmt(node.init)
            cond_e   = self.build_expr(node.condition)
            upd_e    = self._build_update_expr(node.update)
            body_c   = self._build_compound(node.body)
            return c_ast.For(init=init_s, cond=cond_e, next=upd_e, stmt=body_c)

        # ── R15 — while loop ──────────────────────────────────────────────────
        if isinstance(node, JWhileNode):
            return c_ast.While(
                cond=self.build_expr(node.condition),
                stmt=self._build_compound(node.body)
            )

        # ── R16 — do-while ────────────────────────────────────────────────────
        if isinstance(node, JDoWhileNode):
            return c_ast.DoWhile(
                cond=self.build_expr(node.condition),
                stmt=self._build_compound(node.body)
            )

        # ── R17 — System.out.println / printf ─────────────────────────────────
        if isinstance(node, JPrintlnNode):
            self.has_printf = True
            return self._build_printf(node)

        # ── R18 — return ──────────────────────────────────────────────────────
        if isinstance(node, JReturnNode):
            val = self.build_expr(node.value) if node.value else None
            return c_ast.Return(val)

        # ── R19 — Method call as statement ────────────────────────────────────
        if isinstance(node, JMethodCallStmtNode):
            args = [self.build_expr(a) for a in node.args]
            return c_ast.FuncCall(
                name=c_ast.ID(node.name),
                args=c_ast.ExprList(args) if args else None
            )

        # ── R20 — HashMap declaration ─────────────────────────────────────────
        if isinstance(node, JHashMapDeclNode):
            self.has_hashmap = True
            self.hashmap_maps[node.name] = (node.key_type, node.val_type)
            # HashMap<Integer,Integer> map → HashMap map;
            return c_ast.Decl(
                name=node.name, quals=[], align=[], storage=[], funcspec=[],
                type=c_ast.TypeDecl(node.name, [], None,
                                    c_ast.IdentifierType(['HashMap'])),
                init=c_ast.FuncCall(c_ast.ID('hashmap_create'), None),
                bitsize=None
            )

        # ── R21 — map.put(k, v) ───────────────────────────────────────────────
        if isinstance(node, JMapPutNode):
            self.has_hashmap = True
            return c_ast.FuncCall(
                name=c_ast.ID('hashmap_put'),
                args=c_ast.ExprList([
                    c_ast.ID(node.map_name),
                    self.build_expr(node.key),
                    self.build_expr(node.value)
                ])
            )

        return None  # skip unknown nodes

    # ═══════════════════════════════════════════════════════════════════════════
    #  Build a C AST expression node from a Java AST expression node
    # ═══════════════════════════════════════════════════════════════════════════
    def build_expr(self, node):
        if node is None:
            return None

        if isinstance(node, JIntLiteralNode):
            return c_ast.Constant('int', node.value)

        if isinstance(node, JFloatLiteralNode):
            return c_ast.Constant('float', node.value)

        if isinstance(node, JCharLiteralNode):
            return c_ast.Constant('char', node.value)

        if isinstance(node, JStringLiteralNode):
            return c_ast.Constant('string', node.value)

        if isinstance(node, JBoolLiteralNode):
            return c_ast.Constant('int', '1' if node.value == 'true' else '0')

        if isinstance(node, JIDNode):
            return c_ast.ID(node.name)

        # ── R23 — Binary operations ───────────────────────────────────────────
        if isinstance(node, JBinOpNode):
            return c_ast.BinaryOp(
                op=node.op,
                left=self.build_expr(node.left),
                right=self.build_expr(node.right)
            )

        # Unary operations
        if isinstance(node, JUnaryOpNode):
            return c_ast.UnaryOp(op=node.op, expr=self.build_expr(node.operand))

        # ── R8 — 1D array access ──────────────────────────────────────────────
        if isinstance(node, JArrayAccessNode):
            return c_ast.ArrayRef(
                name=c_ast.ID(node.name),
                subscript=self.build_expr(node.index)
            )

        # ── R9 — 2D array access ──────────────────────────────────────────────
        if isinstance(node, JArray2DAccessNode):
            return c_ast.ArrayRef(
                name=c_ast.ArrayRef(
                    name=c_ast.ID(node.name),
                    subscript=self.build_expr(node.row)
                ),
                subscript=self.build_expr(node.col)
            )

        # Function call expression
        if isinstance(node, JMethodCallExprNode):
            args = [self.build_expr(a) for a in node.args]
            return c_ast.FuncCall(
                name=c_ast.ID(node.name),
                args=c_ast.ExprList(args) if args else None
            )

        # ── R22 — map.get(key) ────────────────────────────────────────────────
        if isinstance(node, JMapGetNode):
            self.has_hashmap = True
            return c_ast.FuncCall(
                name=c_ast.ID('hashmap_get'),
                args=c_ast.ExprList([c_ast.ID(node.map_name),
                                     self.build_expr(node.key)])
            )

        if isinstance(node, JMapContainsNode):
            self.has_hashmap = True
            return c_ast.FuncCall(
                name=c_ast.ID('hashmap_contains'),
                args=c_ast.ExprList([c_ast.ID(node.map_name),
                                     self.build_expr(node.key)])
            )

        raise NotImplementedError(f'No build_expr for {type(node).__name__}')

    # ── Helper: build pycparser If node ──────────────────────────────────────
    def _build_if(self, node):
        # Build from last branch backwards (nested if-else chain)
        result = None
        if node.else_block:
            result = self._build_compound(node.else_block)

        for cond, body in reversed(node.branches):
            result = c_ast.If(
                cond=self.build_expr(cond),
                iftrue=self._build_compound(body),
                iffalse=result
            )
        return result

    # ── Helper: build compound block ─────────────────────────────────────────
    def _build_compound(self, block_node):
        stmts = []
        for stmt in block_node.statements:
            c_stmt = self.build_stmt(stmt)
            if c_stmt is not None:
                stmts.append(c_stmt)
        return c_ast.Compound(stmts)

    # ── Helper: for loop update expression ───────────────────────────────────
    def _build_update_expr(self, upd):
        if upd.op == '++':
            return c_ast.UnaryOp('p++', c_ast.ID(upd.name))
        if upd.op == '--':
            return c_ast.UnaryOp('p--', c_ast.ID(upd.name))
        return c_ast.Assignment(
            op=upd.op,
            lvalue=c_ast.ID(upd.name),
            rvalue=self.build_expr(upd.value)
        )

    # ── Helper: R17 — System.out.println → printf ─────────────────────────────
    def _build_printf(self, node):
        self.has_printf = True

        if node.is_printf:
            # System.out.printf("fmt", args) → printf("fmt_converted", args)
            fmt = node.format_str[1:-1].replace('%n', '\\n')
            fmt_node = c_ast.Constant('string', f'"{fmt}"')
            args = [fmt_node] + [self.build_expr(a) for a in node.args]
            return c_ast.FuncCall(c_ast.ID('printf'),
                                  c_ast.ExprList(args))

        # System.out.println(x)  → figure out format from arg type
        if not node.args:
            return c_ast.FuncCall(
                c_ast.ID('printf'),
                c_ast.ExprList([c_ast.Constant('string', '"\\n"')])
            )

        arg = node.args[0]

        # String literal → printf("%s\n", "text") or printf("text\n")
        if isinstance(arg, JStringLiteralNode):
            raw   = arg.value[1:-1]  # strip quotes
            clean = raw.replace('%n', '\\n')
            return c_ast.FuncCall(
                c_ast.ID('printf'),
                c_ast.ExprList([c_ast.Constant('string', f'"{clean}\\n"')])
            )

        # Char → %c
        if isinstance(arg, JCharLiteralNode):
            return c_ast.FuncCall(
                c_ast.ID('printf'),
                c_ast.ExprList([
                    c_ast.Constant('string', '"%c\\n"'),
                    self.build_expr(arg)
                ])
            )

        # Float literal → %f
        if isinstance(arg, JFloatLiteralNode):
            return c_ast.FuncCall(
                c_ast.ID('printf'),
                c_ast.ExprList([
                    c_ast.Constant('string', '"%f\\n"'),
                    self.build_expr(arg)
                ])
            )

        # Default → %d  (int, variable, expression)
        return c_ast.FuncCall(
            c_ast.ID('printf'),
            c_ast.ExprList([
                c_ast.Constant('string', '"%d\\n"'),
                self.build_expr(arg)
            ])
        )

    # ── Helper: Java type → C type ────────────────────────────────────────────
    def translate_type(self, java_type):
        mapping = {
            'int'    : 'int',
            'float'  : 'float',
            'double' : 'double',
            'char'   : 'char',
            'void'   : 'void',
            'boolean': 'int',    # C has no bool — use int
            'String' : 'char*',
        }
        return mapping.get(java_type, java_type)

    # ── HashMap struct helper code ────────────────────────────────────────────
    def _hashmap_struct_code(self):
        return """
/* ── HashMap simulation (generated by Java→C translator) ── */
#define HASHMAP_SIZE 100

typedef struct {
    int keys[HASHMAP_SIZE];
    int vals[HASHMAP_SIZE];
    int count;
} HashMap;

HashMap hashmap_create() {
    HashMap m;
    m.count = 0;
    return m;
}

void hashmap_put(HashMap *m, int key, int val) {
    for (int i = 0; i < m->count; i++) {
        if (m->keys[i] == key) { m->vals[i] = val; return; }
    }
    m->keys[m->count] = key;
    m->vals[m->count] = val;
    m->count++;
}

int hashmap_get(HashMap *m, int key) {
    for (int i = 0; i < m->count; i++) {
        if (m->keys[i] == key) return m->vals[i];
    }
    return -1;
}

int hashmap_contains(HashMap *m, int key) {
    for (int i = 0; i < m->count; i++) {
        if (m->keys[i] == key) return 1;
    }
    return 0;
}
/* ─────────────────────────────────────────────────────────── */
"""
