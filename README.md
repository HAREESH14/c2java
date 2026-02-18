# C → Java Translator (Pure Python)
### Academic / Research Project — No external libraries needed

---

## How to Run

```bash
# Basic translation
python3 src/main.py test/test1_variables_ifelse.c

# Show the AST tree (great for report!)
python3 src/main.py test/test4_functions.c --ast

# Show all tokens from the lexer
python3 src/main.py test/test2_loops.c --tokens

# Run built-in demo (no file needed)
python3 src/main.py

# Show everything
python3 src/main.py test/test3_arrays.c --ast --tokens
```

Output is saved to `Main.java` automatically.

---

## Project Structure

```
c2java_python/
│
├── src/
│   ├── main.py          ← Entry point — runs the full pipeline
│   ├── lexer.py         ← Tokenizer (Lexer)
│   ├── parser.py        ← Recursive Descent Parser → builds AST
│   ├── ast_nodes.py     ← All AST node classes (data structures)
│   ├── visitor.py       ← CToJavaVisitor — 22 translation rules
│   └── ast_printer.py   ← Prints AST as a tree (for reports)
│
├── test/
│   ├── test1_variables_ifelse.c
│   ├── test2_loops.c
│   ├── test3_arrays.c
│   └── test4_functions.c
│
└── README.md
```

---

## Pipeline

```
C Source (.c file)
       │
       ▼
  lexer.py          ← Reads characters → produces Token list
  (Lexer)               e.g. [Token(int), Token(ID,'x'), Token(=), ...]
       │
       ▼
  parser.py         ← Reads tokens → builds AST
  (Parser)              Recursive Descent — one method per grammar rule
       │
       ▼
  AST               ← Tree of ASTNode objects
  (ast_nodes.py)        e.g. ProgramNode → FunctionNode → BlockNode → ...
       │
       ▼
  visitor.py        ← Walks AST node by node → emits Java strings
  (Visitor)             visit_VarDeclNode(), visit_ForNode(), etc.
       │
       ▼
  Main.java         ← Semantically equivalent Java program
```

---

## 22 Translation Rules

| Rule | C | Java |
|------|---|------|
| R1  | Program | `public class Main { }` |
| R2  | `int add(int a, int b)` | `public static int add(int a, int b)` |
| R3  | `int main()` | `public static void main(String[] args)` |
| R4  | `int x = 5;` | `int x = 5;` |
| R5  | `int arr[5];` | `int[] arr = new int[5];` |
| R6  | `int arr[] = {1,2,3};` | `int[] arr = {1, 2, 3};` |
| R7  | `int m[3][3];` | `int[][] m = new int[3][3];` |
| R8  | `arr[i]` | `arr[i]` |
| R9  | `m[i][j]` | `m[i][j]` |
| R10 | `x = expr;` | `x = expr;` |
| R11 | `arr[i] = expr;` | `arr[i] = expr;` |
| R12 | `m[i][j] = expr;` | `m[i][j] = expr;` |
| R13 | `if/else if/else` | `if/else if/else` |
| R14 | `for (init;cond;upd)` | `for (init;cond;upd)` |
| R15 | `while (cond)` | `while (cond)` |
| R16 | `do {} while (cond);` | `do {} while (cond);` |
| R17a| `printf("text\n")` | `System.out.println("text")` |
| R17b| `printf("%d", x)` | `System.out.println(x)` |
| R17c| `printf("v=%d\n", x)` | `System.out.printf("v=%d%n", x)` |
| R18 | `return 0;` (main) | `return;` |
| R19 | `myFunc(a, b);` | `myFunc(a, b);` |
| R20 | `+, -, *, /, %, ==, !=, <, >, <=, >=, &&, \|\|` | same |
| R21 | `!expr` | `!expr` |
| R22 | `int/float/double/char/void` | same |

---

## Key Files Explained

### `lexer.py` — Tokenizer
Reads C source character by character and produces tokens.
```
"int x = 5;"  →  [Token(int), Token(ID,'x'), Token(=), Token(INT_LIT,'5'), Token(;)]
```

### `ast_nodes.py` — AST Data Structures
Plain Python classes, one per grammar construct:
```python
class ForNode(ASTNode):
    def __init__(self, init, condition, update, body):
        self.init      = init       # VarDeclNode or AssignNode
        self.condition = condition  # expression
        self.update    = update     # UpdateNode
        self.body      = body       # BlockNode
```

### `parser.py` — Recursive Descent Parser
One `parse_xxx()` method per grammar rule:
```python
def parse_for(self):
    self.expect('for')
    self.expect('(')
    init = self.parse_for_init()
    ...
    return ForNode(init, cond, update, body)
```

### `visitor.py` — Translation Rules
One `visit_Xxx()` method per AST node type:
```python
def visit_ForNode(self, node):
    return f'for ({init}; {cond}; {upd}) {body}'
```

### `ast_printer.py` — AST Display
Prints the AST as a tree (use `--ast` flag):
```
ProgramNode
└── FunctionNode  int main() [main]
    └── BlockNode  (3 statements)
        ├── VarDeclNode  int x
        │   └── IntLiteral  5
        ├── ForNode
        │   ├── VarDeclNode  int i
        ...
```

---

## Requirements

- Python 3.6 or higher
- No external packages needed

---

## References

- Dragon Book: Aho, Lam, Sethi, Ullman — "Compilers: Principles, Techniques, Tools"
- "Engineering a Compiler" — Cooper & Torczon
- Recursive Descent Parsing: https://en.wikipedia.org/wiki/Recursive_descent_parser
