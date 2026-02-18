# ─────────────────────────────────────────────────────────────────────────────
#  ast_printer.py
#  Prints the AST as a readable tree to the console.
#  Great for your academic report — shows the structure visually.
# ─────────────────────────────────────────────────────────────────────────────

from ast_nodes import *


class ASTPrinter:

    def __init__(self):
        self.lines = []

    def print(self, node, prefix='', is_last=True):
        connector = '└── ' if is_last else '├── '
        child_prefix = prefix + ('    ' if is_last else '│   ')

        label = self._label(node)
        self.lines.append(prefix + connector + label)

        children = self._children(node)
        for i, child in enumerate(children):
            last = (i == len(children) - 1)
            if isinstance(child, ASTNode):
                self.print(child, child_prefix, last)
            else:
                # Leaf value
                conn2 = '└── ' if last else '├── '
                self.lines.append(child_prefix + conn2 + str(child))

    def get_tree(self, root):
        self.lines = []
        self.lines.append('ProgramNode')
        for i, fn in enumerate(root.functions):
            last = (i == len(root.functions) - 1)
            self.print(fn, '', last)
        return '\n'.join(self.lines)

    def _label(self, node):
        if isinstance(node, FunctionNode):
            tag = '[main]' if node.is_main else ''
            return f'FunctionNode  {node.return_type} {node.name}() {tag}'
        if isinstance(node, ParamNode):
            arr = '[]' if node.is_array else ''
            return f'ParamNode  {node.type_} {node.name}{arr}'
        if isinstance(node, BlockNode):
            return f'BlockNode  ({len(node.statements)} statements)'
        if isinstance(node, VarDeclNode):
            return f'VarDeclNode  {node.type_} {node.name}'
        if isinstance(node, ArrayDeclNode):
            size = node.size or 'init'
            return f'ArrayDeclNode  {node.type_}[] {node.name}[{size}]'
        if isinstance(node, ArrayDecl2DNode):
            return f'ArrayDecl2DNode  {node.type_}[][] {node.name}[{node.rows}][{node.cols}]'
        if isinstance(node, AssignNode):
            return f'AssignNode  {node.name} ='
        if isinstance(node, CompoundAssignNode):
            return f'CompoundAssignNode  {node.name} {node.op}'
        if isinstance(node, ArrayAssignNode):
            return f'ArrayAssignNode  {node.name}[i] ='
        if isinstance(node, ArrayAssign2DNode):
            return f'ArrayAssign2DNode  {node.name}[i][j] ='
        if isinstance(node, IfNode):
            return f'IfNode  ({len(node.branches)} branch(es))'
        if isinstance(node, ForNode):
            return 'ForNode'
        if isinstance(node, WhileNode):
            return 'WhileNode'
        if isinstance(node, DoWhileNode):
            return 'DoWhileNode'
        if isinstance(node, BreakNode):
            return 'BreakNode'
        if isinstance(node, ContinueNode):
            return 'ContinueNode'
        if isinstance(node, SwitchNode):
            return f'SwitchNode  ({len(node.cases)} cases)'
        if isinstance(node, CaseNode):
            return f'CaseNode  case {self._label(node.value)}:'
        if isinstance(node, DefaultCaseNode):
            return f'DefaultCaseNode  default:'
        if isinstance(node, PrintNode):
            return f'PrintNode  printf({node.format_str})'
        if isinstance(node, ScanfNode):
            return f'ScanfNode  scanf({node.format_str})'
        if isinstance(node, ReturnNode):
            return 'ReturnNode'
        if isinstance(node, FuncCallStmtNode):
            return f'FuncCallStmtNode  {node.name}(...)'
        if isinstance(node, BinOpNode):
            return f'BinOpNode  [{node.op}]'
        if isinstance(node, UnaryOpNode):
            return f'UnaryOpNode  [{node.op}]'
        if isinstance(node, TernaryNode):
            return 'TernaryNode  [? :]'
        if isinstance(node, ArrayAccessNode):
            return f'ArrayAccessNode  {node.name}[i]'
        if isinstance(node, ArrayAccess2DNode):
            return f'ArrayAccess2DNode  {node.name}[i][j]'
        if isinstance(node, FuncCallExprNode):
            return f'FuncCallExprNode  {node.name}(...)'
        if isinstance(node, IntLiteralNode):
            return f'IntLiteral  {node.value}'
        if isinstance(node, FloatLiteralNode):
            return f'FloatLiteral  {node.value}'
        if isinstance(node, CharLiteralNode):
            return f'CharLiteral  {node.value}'
        if isinstance(node, StringLiteralNode):
            return f'StringLiteral  {node.value}'
        if isinstance(node, IDNode):
            return f'ID  {node.name}'
        if isinstance(node, UpdateNode):
            return f'UpdateNode  {node.name} {node.op}'
        return type(node).__name__

    def _children(self, node):
        if isinstance(node, FunctionNode):
            return node.params + [node.body]
        if isinstance(node, BlockNode):
            return node.statements
        if isinstance(node, VarDeclNode):
            return [node.initializer] if node.initializer else []
        if isinstance(node, ArrayDeclNode):
            return node.init_values or []
        if isinstance(node, AssignNode):
            return [node.value]
        if isinstance(node, CompoundAssignNode):
            return [node.value]
        if isinstance(node, ArrayAssignNode):
            return [node.index, node.value]
        if isinstance(node, ArrayAssign2DNode):
            return [node.row, node.col, node.value]
        if isinstance(node, IfNode):
            children = []
            for cond, body in node.branches:
                children += [cond, body]
            if node.else_block:
                children.append(node.else_block)
            return children
        if isinstance(node, ForNode):
            return [node.init, node.condition, node.update, node.body]
        if isinstance(node, WhileNode):
            return [node.condition, node.body]
        if isinstance(node, DoWhileNode):
            return [node.body, node.condition]
        if isinstance(node, SwitchNode):
            return [node.expr] + node.cases
        if isinstance(node, CaseNode):
            return node.statements
        if isinstance(node, DefaultCaseNode):
            return node.statements
        if isinstance(node, PrintNode):
            return node.args
        if isinstance(node, ScanfNode):
            return []
        if isinstance(node, ReturnNode):
            return [node.value] if node.value else []
        if isinstance(node, FuncCallStmtNode):
            return node.args
        if isinstance(node, BinOpNode):
            return [node.left, node.right]
        if isinstance(node, UnaryOpNode):
            return [node.operand]
        if isinstance(node, TernaryNode):
            return [node.condition, node.then_expr, node.else_expr]
        if isinstance(node, ArrayAccessNode):
            return [node.index]
        if isinstance(node, ArrayAccess2DNode):
            return [node.row, node.col]
        if isinstance(node, FuncCallExprNode):
            return node.args
        if isinstance(node, UpdateNode):
            return [node.value] if node.value else []
        return []
