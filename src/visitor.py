# ─────────────────────────────────────────────────────────────────────────────
#  visitor.py
#  CToJavaVisitor — walks the AST and emits Java source code.
#
#  Each visit_Xxx() method = one translation rule.
#
#  Translation Rules:
#    R1  Program         → public class Main { }
#    R2  FunctionNode    → public static returnType name(params) { }
#    R3  main()          → public static void main(String[] args) { }
#    R4  VarDeclNode     → type name = value;
#    R5  ArrayDeclNode   → type[] name = new type[size];
#    R6  ArrayDeclNode   → type[] name = {v1, v2, v3};     (with initializer)
#    R7  ArrayDecl2D     → type[][] name = new type[r][c];
#    R8  ArrayAccess     → name[index]                      (same in Java)
#    R9  ArrayAccess2D   → name[row][col]                   (same in Java)
#    R10 AssignNode      → name = value;
#    R11 ArrayAssign     → name[i] = value;
#    R12 ArrayAssign2D   → name[i][j] = value;
#    R13 IfNode          → if/else if/else
#    R14 ForNode         → for (init; cond; update) { }
#    R15 WhileNode       → while (cond) { }
#    R16 DoWhileNode     → do { } while (cond);
#    R17 PrintNode       → System.out.println / printf
#    R18 ReturnNode      → return expr;
#    R19 FuncCallStmt    → name(args);
#    R20 BinOpNode       → left op right
#    R21 UnaryOpNode     → !expr
#    R22 Type mapping    → C types → Java types
# ─────────────────────────────────────────────────────────────────────────────

from ast_nodes import *


class CToJavaVisitor:

    def __init__(self):
        self.indent_level = 0
        self.needs_hashmap = False

    def indent(self):
        return '    ' * self.indent_level

    def visit(self, node):
        method = 'visit_' + type(node).__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise NotImplementedError(f'No visitor for {type(node).__name__}')

    # ═══════════════════════════════════════════════════════════════════════
    #  R1 — Program → public class Main { }
    # ═══════════════════════════════════════════════════════════════════════
    def visit_ProgramNode(self, node):
        lines = []

        if self.needs_hashmap:
            lines.append('import java.util.HashMap;')
            lines.append('import java.util.Map;')
            lines.append('')

        lines.append('public class Main {')
        lines.append('')

        self.indent_level = 1
        for fn in node.functions:
            lines.append(self.visit(fn))
            lines.append('')

        lines.append('}')
        return '\n'.join(lines)

    # ═══════════════════════════════════════════════════════════════════════
    #  R2 — Function → public static returnType name(params) { body }
    #  R3 — main()   → public static void main(String[] args) { body }
    # ═══════════════════════════════════════════════════════════════════════
    def visit_FunctionNode(self, node):
        self.indent_level = 1
        ind = self.indent()

        params_str = ', '.join(self.visit(p) for p in node.params)

        if node.is_main:
            header = f'{ind}public static void main(String[] args)'
        else:
            ret = self.translate_type(node.return_type)
            header = f'{ind}public static {ret} {node.name}({params_str})'

        body = self.visit(node.body)
        return f'{header} {body}'

    def visit_ParamNode(self, node):
        t = self.translate_type(node.type_)
        if node.is_array:
            return f'{t}[] {node.name}'
        return f'{t} {node.name}'

    # ═══════════════════════════════════════════════════════════════════════
    #  Block { statements }
    # ═══════════════════════════════════════════════════════════════════════
    def visit_BlockNode(self, node):
        lines = ['{']
        self.indent_level += 1
        for stmt in node.statements:
            lines.append(self.indent() + self.visit(stmt))
        self.indent_level -= 1
        lines.append(self.indent() + '}')
        return '\n'.join(lines)

    # ═══════════════════════════════════════════════════════════════════════
    #  R4 — Variable declaration
    #  int x = 5;   →   int x = 5;
    #  float y;     →   float y;
    # ═══════════════════════════════════════════════════════════════════════
    def visit_VarDeclNode(self, node):
        t = self.translate_type(node.type_)
        if node.initializer is not None:
            return f'{t} {node.name} = {self.visit(node.initializer)};'
        return f'{t} {node.name};'

    # ═══════════════════════════════════════════════════════════════════════
    #  R5 — 1D Array (no init):  int arr[5]  →  int[] arr = new int[5];
    #  R6 — 1D Array (with init): int arr[]={1,2,3}  →  int[] arr = {1,2,3};
    # ═══════════════════════════════════════════════════════════════════════
    def visit_ArrayDeclNode(self, node):
        t = self.translate_type(node.type_)
        if node.init_values is not None:
            vals = ', '.join(self.visit(v) for v in node.init_values)
            return f'{t}[] {node.name} = {{{vals}}};'
        elif node.size is not None:
            return f'{t}[] {node.name} = new {t}[{node.size}];'
        else:
            return f'{t}[] {node.name};'

    # ═══════════════════════════════════════════════════════════════════════
    #  R7 — 2D Array:  int m[3][3]  →  int[][] m = new int[3][3];
    # ═══════════════════════════════════════════════════════════════════════
    def visit_ArrayDecl2DNode(self, node):
        t = self.translate_type(node.type_)
        return f'{t}[][] {node.name} = new {t}[{node.rows}][{node.cols}];'

    # ═══════════════════════════════════════════════════════════════════════
    #  R10 — Assignment:  x = expr;
    # ═══════════════════════════════════════════════════════════════════════
    def visit_AssignNode(self, node):
        return f'{node.name} = {self.visit(node.value)};'

    # ═══════════════════════════════════════════════════════════════════════
    #  R11 — Array assignment:  arr[i] = expr;  (same in Java)
    # ═══════════════════════════════════════════════════════════════════════
    def visit_ArrayAssignNode(self, node):
        return f'{node.name}[{self.visit(node.index)}] = {self.visit(node.value)};'

    # ═══════════════════════════════════════════════════════════════════════
    #  R12 — 2D Array assignment:  m[i][j] = expr;  (same in Java)
    # ═══════════════════════════════════════════════════════════════════════
    def visit_ArrayAssign2DNode(self, node):
        return (f'{node.name}[{self.visit(node.row)}]'
                f'[{self.visit(node.col)}] = {self.visit(node.value)};')

    # ═══════════════════════════════════════════════════════════════════════
    #  R13 — if / else if / else
    # ═══════════════════════════════════════════════════════════════════════
    def visit_IfNode(self, node):
        parts = []
        for i, (cond, body) in enumerate(node.branches):
            prefix = 'if' if i == 0 else 'else if'
            parts.append(f'{prefix} ({self.visit(cond)}) {self.visit(body)}')
        if node.else_block:
            parts.append(f'else {self.visit(node.else_block)}')
        return ' '.join(parts)

    # ═══════════════════════════════════════════════════════════════════════
    #  R14 — for loop  (same syntax in Java)
    # ═══════════════════════════════════════════════════════════════════════
    def visit_ForNode(self, node):
        # Init — strip the semicolon since for() provides it
        init_str = self.visit(node.init).rstrip(';')
        cond_str = self.visit(node.condition)
        upd_str  = self.visit_UpdateNode(node.update)
        body_str = self.visit(node.body)
        return f'for ({init_str}; {cond_str}; {upd_str}) {body_str}'

    def visit_UpdateNode(self, node):
        if node.op in ('++', '--'):
            return f'{node.name}{node.op}'
        return f'{node.name} {node.op} {self.visit(node.value)}'

    # ═══════════════════════════════════════════════════════════════════════
    #  R15 — while loop  (identical in Java)
    # ═══════════════════════════════════════════════════════════════════════
    def visit_WhileNode(self, node):
        return f'while ({self.visit(node.condition)}) {self.visit(node.body)}'

    # ═══════════════════════════════════════════════════════════════════════
    #  R16 — do-while loop  (identical in Java)
    # ═══════════════════════════════════════════════════════════════════════
    def visit_DoWhileNode(self, node):
        return f'do {self.visit(node.body)} while ({self.visit(node.condition)});'

    # ═══════════════════════════════════════════════════════════════════════
    #  R17 — printf → System.out.println / System.out.printf
    #
    #  printf("hello\n")       → System.out.println("hello")
    #  printf("%d", x)         → System.out.println(x)
    #  printf("v=%d\n", x)     → System.out.printf("v=%d%n", x)
    # ═══════════════════════════════════════════════════════════════════════
    def visit_PrintNode(self, node):
        raw   = node.format_str          # includes quotes: "hello\n"
        inner = raw[1:-1]                # strip quotes →  hello\n

        # No args — pure string
        if not node.args:
            if inner.endswith('\\n'):
                clean = inner[:-2]
                return f'System.out.println("{clean}");'
            return f'System.out.print("{inner}");'

        args_str = ', '.join(self.visit(a) for a in node.args)

        # Single bare format specifier → println(arg)
        bare_specs = {'%d', '%f', '%lf', '%c', '%s'}
        if len(node.args) == 1 and inner in bare_specs:
            return f'System.out.println({args_str});'

        # Complex format → printf, replace \n with %n
        java_fmt = inner.replace('\\n', '%n')
        return f'System.out.printf("{java_fmt}", {args_str});'

    # ═══════════════════════════════════════════════════════════════════════
    #  R18 — return
    #  return 0; in main → return;
    #  return x; in other functions → return x;
    # ═══════════════════════════════════════════════════════════════════════
    def visit_ReturnNode(self, node):
        if node.value is None:
            return 'return;'
        val = self.visit(node.value)
        # return 0 in main → just return
        if val == '0' and self.indent_level == 2:
            return 'return;'
        return f'return {val};'

    # ═══════════════════════════════════════════════════════════════════════
    #  R19 — Function call statement:  myFunc(a, b);
    # ═══════════════════════════════════════════════════════════════════════
    def visit_FuncCallStmtNode(self, node):
        args = ', '.join(self.visit(a) for a in node.args)
        return f'{node.name}({args});'

    # ═══════════════════════════════════════════════════════════════════════
    #  R20 — Binary operations  (same operators in Java)
    # ═══════════════════════════════════════════════════════════════════════
    def visit_BinOpNode(self, node):
        return f'{self.visit(node.left)} {node.op} {self.visit(node.right)}'

    # ═══════════════════════════════════════════════════════════════════════
    #  R21 — Unary operations
    # ═══════════════════════════════════════════════════════════════════════
    def visit_UnaryOpNode(self, node):
        return f'{node.op}{self.visit(node.operand)}'

    # ── R8 — 1D Array access ──────────────────────────────────────────────
    def visit_ArrayAccessNode(self, node):
        return f'{node.name}[{self.visit(node.index)}]'

    # ── R9 — 2D Array access ──────────────────────────────────────────────
    def visit_ArrayAccess2DNode(self, node):
        return f'{node.name}[{self.visit(node.row)}][{self.visit(node.col)}]'

    # ── Function call expression ──────────────────────────────────────────
    def visit_FuncCallExprNode(self, node):
        args = ', '.join(self.visit(a) for a in node.args)
        return f'{node.name}({args})'

    # ── Literals ──────────────────────────────────────────────────────────
    def visit_IntLiteralNode(self, node):
        return node.value

    def visit_FloatLiteralNode(self, node):
        return node.value + 'f'     # Java needs 'f' suffix for float literals

    def visit_CharLiteralNode(self, node):
        return node.value           # 'A' → 'A'  (same in Java)

    def visit_StringLiteralNode(self, node):
        return node.value           # "hello" → "hello"

    def visit_IDNode(self, node):
        return node.name

    # ═══════════════════════════════════════════════════════════════════════
    #  R22 — Type mapping  (C → Java)
    # ═══════════════════════════════════════════════════════════════════════
    def translate_type(self, c_type):
        mapping = {
            'int'   : 'int',
            'float' : 'float',
            'double': 'double',
            'char'  : 'char',
            'void'  : 'void',
        }
        return mapping.get(c_type, c_type)
