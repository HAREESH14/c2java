# ─────────────────────────────────────────────────────────────────────────────
#  ast_nodes.py
#  All AST node classes.
#  Each class = one grammar construct in C.
# ─────────────────────────────────────────────────────────────────────────────


class ASTNode:
    """Base class for all AST nodes."""
    pass


# ── Program ───────────────────────────────────────────────────────────────────
class ProgramNode(ASTNode):
    """Root of the AST. Contains all functions."""
    def __init__(self, functions):
        self.functions = functions   # list of FunctionNode


# ── Functions ─────────────────────────────────────────────────────────────────
class FunctionNode(ASTNode):
    """
    A function declaration.
    e.g.  int add(int a, int b) { return a + b; }
    """
    def __init__(self, return_type, name, params, body, is_main=False):
        self.return_type = return_type   # str: 'int', 'void', etc.
        self.name        = name          # str
        self.params      = params        # list of ParamNode
        self.body        = body          # BlockNode
        self.is_main     = is_main       # bool


class ParamNode(ASTNode):
    """Function parameter. e.g.  int a   OR   int arr[]"""
    def __init__(self, type_, name, is_array=False):
        self.type_    = type_       # str
        self.name     = name        # str
        self.is_array = is_array    # bool — True if  int arr[]


# ── Statements ────────────────────────────────────────────────────────────────
class BlockNode(ASTNode):
    """A block of statements enclosed in { }"""
    def __init__(self, statements):
        self.statements = statements   # list of ASTNode


class VarDeclNode(ASTNode):
    """Variable declaration.  int x = 5;   OR   float y;"""
    def __init__(self, type_, name, initializer=None):
        self.type_       = type_         # str
        self.name        = name          # str
        self.initializer = initializer   # expression ASTNode or None


class ArrayDeclNode(ASTNode):
    """
    1D array declaration.
    int arr[5];              → size=5,  init_values=None
    int arr[] = {1, 2, 3};  → size=None, init_values=[...]
    """
    def __init__(self, type_, name, size=None, init_values=None):
        self.type_       = type_          # str
        self.name        = name           # str
        self.size        = size           # int literal str or None
        self.init_values = init_values    # list of expr nodes or None


class ArrayDecl2DNode(ASTNode):
    """2D array declaration.  int matrix[3][3];"""
    def __init__(self, type_, name, rows, cols):
        self.type_ = type_   # str
        self.name  = name    # str
        self.rows  = rows    # str
        self.cols  = cols    # str


class AssignNode(ASTNode):
    """Simple assignment.  x = expr;"""
    def __init__(self, name, value):
        self.name  = name    # str
        self.value = value   # expr ASTNode


class CompoundAssignNode(ASTNode):
    """Compound assignment.  x += expr;  x -= expr;  x *= expr;  x /= expr;"""
    def __init__(self, name, op, value):
        self.name  = name    # str
        self.op    = op      # str: '+=', '-=', '*=', '/=', '%='
        self.value = value   # expr ASTNode


class ArrayAssignNode(ASTNode):
    """1D array element assignment.  arr[i] = expr;"""
    def __init__(self, name, index, value):
        self.name  = name    # str
        self.index = index   # expr ASTNode
        self.value = value   # expr ASTNode


class ArrayAssign2DNode(ASTNode):
    """2D array element assignment.  matrix[i][j] = expr;"""
    def __init__(self, name, row, col, value):
        self.name  = name
        self.row   = row
        self.col   = col
        self.value = value


class IfNode(ASTNode):
    """if / else if / else statement."""
    def __init__(self, branches, else_block=None):
        # branches = list of (condition_expr, BlockNode)
        self.branches   = branches
        self.else_block = else_block   # BlockNode or None


class ForNode(ASTNode):
    """for (init; condition; update) { body }"""
    def __init__(self, init, condition, update, body):
        self.init      = init       # VarDeclNode or AssignNode
        self.condition = condition  # expr ASTNode
        self.update    = update     # UpdateNode
        self.body      = body       # BlockNode


class UpdateNode(ASTNode):
    """Loop update expression.  i++  i--  i+=2  i=expr"""
    def __init__(self, name, op, value=None):
        self.name  = name    # str
        self.op    = op      # '++', '--', '+=', '-=', '='
        self.value = value   # expr ASTNode or None


class WhileNode(ASTNode):
    """while (condition) { body }"""
    def __init__(self, condition, body):
        self.condition = condition
        self.body      = body


class DoWhileNode(ASTNode):
    """do { body } while (condition);"""
    def __init__(self, body, condition):
        self.body      = body
        self.condition = condition


class BreakNode(ASTNode):
    """break;"""
    pass


class ContinueNode(ASTNode):
    """continue;"""
    pass


class SwitchNode(ASTNode):
    """switch (expr) { case ...: ... default: ... }"""
    def __init__(self, expr, cases):
        self.expr  = expr    # expr ASTNode
        self.cases = cases   # list of CaseNode / DefaultCaseNode


class CaseNode(ASTNode):
    """case value: statements"""
    def __init__(self, value, statements):
        self.value      = value       # IntLiteralNode or CharLiteralNode
        self.statements = statements  # list of ASTNode


class DefaultCaseNode(ASTNode):
    """default: statements"""
    def __init__(self, statements):
        self.statements = statements  # list of ASTNode


class PrintNode(ASTNode):
    """printf("format", args...)"""
    def __init__(self, format_str, args):
        self.format_str = format_str   # str (with quotes)
        self.args       = args         # list of expr ASTNodes


class ScanfNode(ASTNode):
    """scanf("%d", &x)  — the & is stripped, vars holds variable names."""
    def __init__(self, format_str, vars_):
        self.format_str = format_str   # str (with quotes)
        self.vars_      = vars_        # list of str (variable names, & stripped)


class ReturnNode(ASTNode):
    """return expr;  OR  return;"""
    def __init__(self, value=None):
        self.value = value   # expr ASTNode or None


class FuncCallStmtNode(ASTNode):
    """Function call as a statement.  myFunc(a, b);"""
    def __init__(self, name, args):
        self.name = name
        self.args = args   # list of expr ASTNodes


# ── Expressions ───────────────────────────────────────────────────────────────
class TernaryNode(ASTNode):
    """Ternary expression.  condition ? then_expr : else_expr"""
    def __init__(self, condition, then_expr, else_expr):
        self.condition = condition
        self.then_expr = then_expr
        self.else_expr = else_expr


class BinOpNode(ASTNode):
    """Binary operation.  left OP right"""
    def __init__(self, left, op, right):
        self.left  = left
        self.op    = op     # str: '+', '-', '==', '<', '&&', '&', '|', etc.
        self.right = right


class UnaryOpNode(ASTNode):
    """Unary operation.  !expr  OR  -expr  OR  ~expr"""
    def __init__(self, op, operand):
        self.op      = op
        self.operand = operand


class ArrayAccessNode(ASTNode):
    """1D array access.  arr[i]"""
    def __init__(self, name, index):
        self.name  = name
        self.index = index


class ArrayAccess2DNode(ASTNode):
    """2D array access.  matrix[i][j]"""
    def __init__(self, name, row, col):
        self.name = name
        self.row  = row
        self.col  = col


class FuncCallExprNode(ASTNode):
    """Function call as an expression.  add(x, y)"""
    def __init__(self, name, args):
        self.name = name
        self.args = args


class IntLiteralNode(ASTNode):
    def __init__(self, value):
        self.value = value   # str


class FloatLiteralNode(ASTNode):
    def __init__(self, value):
        self.value = value   # str


class CharLiteralNode(ASTNode):
    def __init__(self, value):
        self.value = value   # str e.g. "'A'"


class StringLiteralNode(ASTNode):
    def __init__(self, value):
        self.value = value   # str e.g. '"hello"'


class IDNode(ASTNode):
    def __init__(self, name):
        self.name = name
