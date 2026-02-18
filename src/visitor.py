# ─────────────────────────────────────────────────────────────────────────────
#  visitor.py
#  CToJavaVisitor — walks the AST and emits Java source code.
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
#    R10b CompoundAssign → name op= value;
#    R11 ArrayAssign     → name[i] = value;
#    R12 ArrayAssign2D   → name[i][j] = value;
#    R13 IfNode          → if/else if/else
#    R14 ForNode         → for (init; cond; update) { }
#    R15 WhileNode       → while (cond) { }
#    R16 DoWhileNode     → do { } while (cond);
#    R17 PrintNode       → System.out.println / printf
#    R17b ScanfNode      → Scanner + sc.nextInt() / sc.nextDouble() / sc.next()
#    R18 ReturnNode      → return expr;
#    R19 FuncCallStmt    → name(args);
#    R20 BinOpNode       → left op right
#    R21 UnaryOpNode     → !expr / -expr / ~expr
#    R22 Type mapping    → C types → Java types
#    R23 BreakNode       → break;
#    R24 ContinueNode    → continue;
#    R25 SwitchNode      → switch (expr) { case ...: ... }
#    R26 TernaryNode     → (cond ? then : else)
# ─────────────────────────────────────────────────────────────────────────────

from ast_nodes import *


class CToJavaVisitor:

    def __init__(self):
        self.indent_level      = 0
        self.needs_scanner     = False   # set True when scanf is encountered
        self._scanner_declared = False   # True after Scanner sc = ... is emitted once
        self._in_main          = False   # Bug 1 Fix: track whether we're inside main()

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
        # First pass: detect if Scanner is needed (any ScanfNode anywhere)
        self._detect_scanner(node)

        lines = []

        if self.needs_scanner:
            lines.append('import java.util.Scanner;')
            lines.append('')

        lines.append('public class Main {')
        lines.append('')

        self.indent_level = 1
        for fn in node.functions:
            lines.append(self.visit(fn))
            lines.append('')

        lines.append('}')
        return '\n'.join(lines)

    def _detect_scanner(self, node):
        """Walk the entire AST to check if any ScanfNode exists."""
        if isinstance(node, ScanfNode):
            self.needs_scanner = True
            return
        for child in self._iter_children(node):
            self._detect_scanner(child)

    def _iter_children(self, node):
        """Yield all child ASTNodes of a node (for scanner detection)."""
        if isinstance(node, ProgramNode):
            yield from node.functions
        elif isinstance(node, FunctionNode):
            yield from node.params
            yield node.body
        elif isinstance(node, BlockNode):
            yield from node.statements
        elif isinstance(node, VarDeclNode):
            if node.initializer: yield node.initializer
        elif isinstance(node, ArrayDeclNode):
            if node.init_values:
                yield from node.init_values
        elif isinstance(node, AssignNode):
            yield node.value
        elif isinstance(node, CompoundAssignNode):
            yield node.value
        elif isinstance(node, ArrayAssignNode):
            yield node.index; yield node.value
        elif isinstance(node, ArrayAssign2DNode):
            yield node.row; yield node.col; yield node.value
        elif isinstance(node, IfNode):
            for cond, body in node.branches:
                yield cond; yield body
            if node.else_block: yield node.else_block
        elif isinstance(node, ForNode):
            yield node.init; yield node.condition; yield node.update; yield node.body
        elif isinstance(node, WhileNode):
            yield node.condition; yield node.body
        elif isinstance(node, DoWhileNode):
            yield node.body; yield node.condition
        elif isinstance(node, SwitchNode):
            yield node.expr; yield from node.cases
        elif isinstance(node, CaseNode):
            yield node.value; yield from node.statements
        elif isinstance(node, DefaultCaseNode):
            yield from node.statements
        elif isinstance(node, PrintNode):
            yield from node.args
        elif isinstance(node, ReturnNode):
            if node.value: yield node.value
        elif isinstance(node, FuncCallStmtNode):
            yield from node.args
        elif isinstance(node, BinOpNode):
            yield node.left; yield node.right
        elif isinstance(node, UnaryOpNode):
            yield node.operand
        elif isinstance(node, TernaryNode):
            yield node.condition; yield node.then_expr; yield node.else_expr
        elif isinstance(node, ArrayAccessNode):
            yield node.index
        elif isinstance(node, ArrayAccess2DNode):
            yield node.row; yield node.col
        elif isinstance(node, FuncCallExprNode):
            yield from node.args
        elif isinstance(node, UpdateNode):
            if node.value: yield node.value

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

        # ── Bug 1 Fix: set _in_main flag so visit_ReturnNode knows context ──
        prev_in_main = self._in_main
        self._in_main = node.is_main

        body = self.visit(node.body)

        self._in_main = prev_in_main
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

        # Declare Scanner only ONCE at the top of the main function body
        if self._in_main and self.needs_scanner and not self._scanner_declared:
            lines.append(self.indent() + 'Scanner sc = new Scanner(System.in);')
            self._scanner_declared = True

        for stmt in node.statements:
            lines.append(self.indent() + self.visit(stmt))

        self.indent_level -= 1
        lines.append(self.indent() + '}')
        return '\n'.join(lines)

    # ═══════════════════════════════════════════════════════════════════════
    #  R4 — Variable declaration
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
    #  R10b — Compound Assignment:  x += expr;  x -= expr;  etc.
    # ═══════════════════════════════════════════════════════════════════════
    def visit_CompoundAssignNode(self, node):
        return f'{node.name} {node.op} {self.visit(node.value)};'

    # ═══════════════════════════════════════════════════════════════════════
    #  R11 — Array assignment:  arr[i] = expr;
    # ═══════════════════════════════════════════════════════════════════════
    def visit_ArrayAssignNode(self, node):
        return f'{node.name}[{self.visit(node.index)}] = {self.visit(node.value)};'

    # ═══════════════════════════════════════════════════════════════════════
    #  R12 — 2D Array assignment:  m[i][j] = expr;
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
    #  R14 — for loop
    # ═══════════════════════════════════════════════════════════════════════
    def visit_ForNode(self, node):
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
    #  R15 — while loop
    # ═══════════════════════════════════════════════════════════════════════
    def visit_WhileNode(self, node):
        return f'while ({self.visit(node.condition)}) {self.visit(node.body)}'

    # ═══════════════════════════════════════════════════════════════════════
    #  R16 — do-while loop
    # ═══════════════════════════════════════════════════════════════════════
    def visit_DoWhileNode(self, node):
        return f'do {self.visit(node.body)} while ({self.visit(node.condition)});'

    # ═══════════════════════════════════════════════════════════════════════
    #  R23 — break
    # ═══════════════════════════════════════════════════════════════════════
    def visit_BreakNode(self, node):
        return 'break;'

    # ═══════════════════════════════════════════════════════════════════════
    #  R24 — continue
    # ═══════════════════════════════════════════════════════════════════════
    def visit_ContinueNode(self, node):
        return 'continue;'

    # ═══════════════════════════════════════════════════════════════════════
    #  R25 — switch / case / default
    # ═══════════════════════════════════════════════════════════════════════
    def visit_SwitchNode(self, node):
        lines = [f'switch ({self.visit(node.expr)}) {{']
        self.indent_level += 1
        for case in node.cases:
            lines.append(self.indent() + self.visit(case))
        self.indent_level -= 1
        lines.append(self.indent() + '}')
        return '\n'.join(lines)

    def visit_CaseNode(self, node):
        lines = [f'case {self.visit(node.value)}:']
        self.indent_level += 1
        for stmt in node.statements:
            lines.append(self.indent() + self.visit(stmt))
        self.indent_level -= 1
        return '\n'.join(lines)

    def visit_DefaultCaseNode(self, node):
        lines = ['default:']
        self.indent_level += 1
        for stmt in node.statements:
            lines.append(self.indent() + self.visit(stmt))
        self.indent_level -= 1
        return '\n'.join(lines)

    # ═══════════════════════════════════════════════════════════════════════
    #  R17 — printf → System.out.println / System.out.printf
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
        bare_specs = {'%d', '%f', '%lf', '%c', '%s', '%ld', '%u'}
        if len(node.args) == 1 and inner.strip() in bare_specs:
            return f'System.out.println({args_str});'

        # Complex format → printf, replace \n with %n
        java_fmt = inner.replace('\\n', '%n')
        return f'System.out.printf("{java_fmt}", {args_str});'

    # ═══════════════════════════════════════════════════════════════════════
    #  R17b — scanf → Scanner.nextInt() / nextDouble() / next()
    # ═══════════════════════════════════════════════════════════════════════
    def visit_ScanfNode(self, node):
        raw   = node.format_str
        inner = raw[1:-1]   # strip quotes

        # Map format specifiers to Scanner methods
        spec_map = {
            '%d':  'sc.nextInt()',
            '%f':  'sc.nextFloat()',
            '%lf': 'sc.nextDouble()',
            '%c':  'sc.next().charAt(0)',
            '%s':  'sc.next()',
            '%ld': 'sc.nextLong()',
            '%u':  'sc.nextInt()',
        }

        # Split format string into specifiers (handles multiple like "%d %d")
        import re
        specs = re.findall(r'%[a-zA-Z]+', inner)

        lines = []
        for var, spec in zip(node.vars_, specs):
            method = spec_map.get(spec, 'sc.nextInt()')
            lines.append(f'{var} = {method};')

        return '\n'.join(lines) if lines else '// scanf (no vars)'

    # ═══════════════════════════════════════════════════════════════════════
    #  R18 — return
    #  Bug 1 Fix: use self._in_main instead of indent_level heuristic
    # ═══════════════════════════════════════════════════════════════════════
    def visit_ReturnNode(self, node):
        if node.value is None:
            return 'return;'
        val = self.visit(node.value)
        # return 0 in main → just return; (correct for void main in Java)
        if val == '0' and self._in_main:
            return 'return;'
        return f'return {val};'

    # ═══════════════════════════════════════════════════════════════════════
    #  R19 — Function call statement:  myFunc(a, b);
    # ═══════════════════════════════════════════════════════════════════════
    def visit_FuncCallStmtNode(self, node):
        args = ', '.join(self.visit(a) for a in node.args)
        return f'{node.name}({args});'

    # ═══════════════════════════════════════════════════════════════════════
    #  R20 — Binary operations
    # ═══════════════════════════════════════════════════════════════════════
    def visit_BinOpNode(self, node):
        return f'{self.visit(node.left)} {node.op} {self.visit(node.right)}'

    # ═══════════════════════════════════════════════════════════════════════
    #  R21 — Unary operations  (!expr, -expr, ~expr)
    # ═══════════════════════════════════════════════════════════════════════
    def visit_UnaryOpNode(self, node):
        return f'{node.op}{self.visit(node.operand)}'

    # ═══════════════════════════════════════════════════════════════════════
    #  R26 — Ternary:  cond ? then : else  →  (cond ? then : else)
    # ═══════════════════════════════════════════════════════════════════════
    def visit_TernaryNode(self, node):
        cond = self.visit(node.condition)
        then = self.visit(node.then_expr)
        els  = self.visit(node.else_expr)
        return f'({cond} ? {then} : {els})'

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
            'int'     : 'int',
            'float'   : 'float',
            'double'  : 'double',
            'char'    : 'char',
            'void'    : 'void',
            'long'    : 'long',
            'short'   : 'short',
            'unsigned': 'int',    # Java has no unsigned; use int
            'bool'    : 'boolean',
        }
        return mapping.get(c_type, c_type)
