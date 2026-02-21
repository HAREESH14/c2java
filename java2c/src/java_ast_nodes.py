# ─────────────────────────────────────────────────────────────────────────────
#  java_ast_nodes.py
#  AST node classes for Java source code.
# ─────────────────────────────────────────────────────────────────────────────

class JNode:
    """Base class for all Java AST nodes."""
    pass

# ── Program ───────────────────────────────────────────────────────────────────
class JProgramNode(JNode):
    """Root: public class Main { methods... }"""
    def __init__(self, class_name, methods):
        self.class_name = class_name
        self.methods    = methods       # list of JMethodNode

# ── Methods ───────────────────────────────────────────────────────────────────
class JMethodNode(JNode):
    """
    public static int add(int a, int b) { body }
    public static void main(String[] args) { body }
    """
    def __init__(self, return_type, name, params, body, is_main=False):
        self.return_type = return_type  # str
        self.name        = name         # str
        self.params      = params       # list of JParamNode
        self.body        = body         # JBlockNode
        self.is_main     = is_main

class JParamNode(JNode):
    """Method parameter: int a   OR   int[] arr"""
    def __init__(self, type_, name, is_array=False):
        self.type_    = type_
        self.name     = name
        self.is_array = is_array

# ── Statements ────────────────────────────────────────────────────────────────
class JBlockNode(JNode):
    def __init__(self, statements):
        self.statements = statements

class JVarDeclNode(JNode):
    """int x = 5;   float y;"""
    def __init__(self, type_, name, initializer=None):
        self.type_       = type_
        self.name        = name
        self.initializer = initializer

class JArrayDeclNode(JNode):
    """
    int[] arr = new int[5];
    int[] arr = {1, 2, 3};
    """
    def __init__(self, type_, name, size=None, init_values=None):
        self.type_       = type_
        self.name        = name
        self.size        = size          # expr node or None
        self.init_values = init_values   # list of expr nodes or None

class JArray2DDeclNode(JNode):
    """int[][] matrix = new int[3][3];"""
    def __init__(self, type_, name, rows, cols):
        self.type_ = type_
        self.name  = name
        self.rows  = rows   # expr
        self.cols  = cols   # expr

class JAssignNode(JNode):
    """x = expr;"""
    def __init__(self, name, value):
        self.name  = name
        self.value = value

class JArrayAssignNode(JNode):
    """arr[i] = expr;"""
    def __init__(self, name, index, value):
        self.name  = name
        self.index = index
        self.value = value

class JArray2DAssignNode(JNode):
    """matrix[i][j] = expr;"""
    def __init__(self, name, row, col, value):
        self.name  = name
        self.row   = row
        self.col   = col
        self.value = value

class JIfNode(JNode):
    """if / else if / else"""
    def __init__(self, branches, else_block=None):
        self.branches   = branches      # list of (cond, JBlockNode)
        self.else_block = else_block

class JForNode(JNode):
    """for (init; cond; update) { body }"""
    def __init__(self, init, condition, update, body):
        self.init      = init
        self.condition = condition
        self.update    = update
        self.body      = body

class JUpdateNode(JNode):
    """i++  i--  i += 2  i = expr"""
    def __init__(self, name, op, value=None):
        self.name  = name
        self.op    = op
        self.value = value

class JWhileNode(JNode):
    """while (cond) { body }"""
    def __init__(self, condition, body):
        self.condition = condition
        self.body      = body

class JDoWhileNode(JNode):
    """do { body } while (cond);"""
    def __init__(self, body, condition):
        self.body      = body
        self.condition = condition

class JPrintlnNode(JNode):
    """System.out.println(expr)  or  System.out.printf(fmt, args)"""
    def __init__(self, args, is_printf=False, format_str=None):
        self.args       = args          # list of expr nodes
        self.is_printf  = is_printf
        self.format_str = format_str    # str with quotes if printf

class JReturnNode(JNode):
    """return expr;  or  return;"""
    def __init__(self, value=None):
        self.value = value

class JMethodCallStmtNode(JNode):
    """methodName(args);"""
    def __init__(self, name, args):
        self.name = name
        self.args = args

# ── HashMap statements ────────────────────────────────────────────────────────
class JHashMapDeclNode(JNode):
    """HashMap<K,V> map = new HashMap<>();"""
    def __init__(self, key_type, val_type, name):
        self.key_type = key_type
        self.val_type = val_type
        self.name     = name

class JMapPutNode(JNode):
    """map.put(key, value);"""
    def __init__(self, map_name, key, value):
        self.map_name = map_name
        self.key      = key
        self.value    = value

class JMapGetNode(JNode):
    """map.get(key) — as expression"""
    def __init__(self, map_name, key):
        self.map_name = map_name
        self.key      = key

class JMapContainsNode(JNode):
    """map.containsKey(key) — as expression"""
    def __init__(self, map_name, key):
        self.map_name = map_name
        self.key      = key

# ── Expressions ───────────────────────────────────────────────────────────────
class JBinOpNode(JNode):
    def __init__(self, left, op, right):
        self.left  = left
        self.op    = op
        self.right = right

class JUnaryOpNode(JNode):
    def __init__(self, op, operand):
        self.op      = op
        self.operand = operand

class JArrayAccessNode(JNode):
    def __init__(self, name, index):
        self.name  = name
        self.index = index

class JArray2DAccessNode(JNode):
    def __init__(self, name, row, col):
        self.name = name
        self.row  = row
        self.col  = col

class JMethodCallExprNode(JNode):
    def __init__(self, name, args):
        self.name = name
        self.args = args

class JIntLiteralNode(JNode):
    def __init__(self, value):
        self.value = value

class JFloatLiteralNode(JNode):
    def __init__(self, value):
        self.value = value

class JCharLiteralNode(JNode):
    def __init__(self, value):
        self.value = value

class JStringLiteralNode(JNode):
    def __init__(self, value):
        self.value = value

class JBoolLiteralNode(JNode):
    def __init__(self, value):
        self.value = value   # 'true' or 'false'

class JIDNode(JNode):
    def __init__(self, name):
        self.name = name
