# Java → C Translator (Python + pycparser)
### Academic / Research Project

---

## External Library Used

| Library | Purpose | Install |
|---------|---------|---------|
| **pycparser** | Builds C AST nodes + emits valid C code | `pip install pycparser` |

pycparser provides two key things:
- `pycparser.c_ast.*` — C AST node classes (Decl, For, If, FuncCall, etc.)
- `pycparser.c_generator.CGenerator` — walks C AST → emits C source text

---

## How to Run

```bash
pip install pycparser

# Basic translation
python3 src/main.py test/test4_functions.java

# Show Java AST structure
python3 src/main.py test/test4_functions.java --ast

# Show tokens
python3 src/main.py test/test2_loops.java --tokens

# Run built-in demo
python3 src/main.py
```

---

## Project Structure

```
java2c/
├── src/
│   ├── main.py               ← Entry point
│   ├── java_lexer.py         ← Tokenizes Java source
│   ├── java_ast_nodes.py     ← Java AST node classes
│   ├── java_parser.py        ← Recursive descent parser for Java
│   └── java_to_c_visitor.py  ← Visits Java AST → builds pycparser C AST → emits C
│
├── test/
│   ├── test1_variables_ifelse.java
│   ├── test2_loops.java
│   ├── test3_arrays.java
│   ├── test4_functions.java
│   └── test5_hashmap.java
│
└── README.md
```

---

## Full Translation Pipeline

```
Java Source (.java)
       │
       ▼
 java_lexer.py         ← Tokenizes Java characters → Token list
       │                  e.g. [Token(public), Token(class), Token(ID,'Main'), ...]
       ▼
 java_parser.py        ← Recursive descent parser → Java AST
       │                  e.g. JProgramNode → JMethodNode → JBlockNode → ...
       ▼
 Java AST              ← Tree of JNode objects (java_ast_nodes.py)
       │
       ▼
 java_to_c_visitor.py  ← Visits each Java node
       │                  Calls build_stmt() / build_expr()
       │                  Returns pycparser c_ast.* nodes
       ▼
 pycparser C AST       ← Tree of c_ast.* objects (EXTERNAL LIBRARY)
       │                  e.g. c_ast.For, c_ast.If, c_ast.FuncDef ...
       ▼
 c_generator.CGenerator ← Walks C AST → emits C source text (EXTERNAL LIBRARY)
       │
       ▼
 C Source (.c file)
```

---

## 23 Translation Rules

| Rule | Java | C |
|------|------|---|
| R1  | `public class Main { }` | `(removed — C has no classes)` |
| R2  | `public static int add(int a, int b)` | `int add(int a, int b)` |
| R3  | `public static void main(String[] args)` | `int main()` |
| R4  | `int x = 5;` | `int x = 5;` |
| R5  | `int[] arr = new int[5];` | `int arr[5];` |
| R6  | `int[] arr = {1, 2, 3};` | `int arr[] = {1, 2, 3};` |
| R7  | `int[][] m = new int[3][3];` | `int m[3][3];` |
| R8  | `arr[i]` | `arr[i]` |
| R9  | `m[i][j]` | `m[i][j]` |
| R10 | `x = expr;` | `x = expr;` |
| R11 | `arr[i] = expr;` | `arr[i] = expr;` |
| R12 | `m[i][j] = expr;` | `m[i][j] = expr;` |
| R13 | `if/else if/else` | `if/else if/else` |
| R14 | `for (init; cond; upd)` | `for (init; cond; upd)` |
| R15 | `while (cond)` | `while (cond)` |
| R16 | `do {} while (cond);` | `do {} while (cond);` |
| R17a| `System.out.println(x)` | `printf("%d\n", x)` |
| R17b| `System.out.println("text")` | `printf("text\n")` |
| R17c| `System.out.printf("fmt%n", x)` | `printf("fmt\n", x)` |
| R18 | `return expr;` | `return expr;` |
| R19 | `myMethod(a, b);` | `myMethod(a, b);` |
| R20 | `HashMap<K,V> map = new HashMap<>()` | `HashMap map = hashmap_create();` |
| R21 | `map.put(key, val)` | `hashmap_put(map, key, val)` |
| R22 | `map.get(key)` | `hashmap_get(map, key)` |
| R23 | `boolean` | `int` (C has no bool) |

---

## HashMap Translation (Key Academic Point)

Java's `HashMap<K,V>` has no direct C equivalent.
The translator generates a C struct-based simulation:

```c
/* Generated automatically when HashMap is detected */
#define HASHMAP_SIZE 100

typedef struct {
    int keys[HASHMAP_SIZE];
    int vals[HASHMAP_SIZE];
    int count;
} HashMap;

HashMap hashmap_create();
void hashmap_put(HashMap *m, int key, int val);
int  hashmap_get(HashMap *m, int key);
int  hashmap_contains(HashMap *m, int key);
```

Then Java:
```java
HashMap<Integer,Integer> map = new HashMap<>();
map.put(101, 95);
int v = map.get(101);
```

Becomes C:
```c
HashMap map = hashmap_create();
hashmap_put(map, 101, 95);
int v = hashmap_get(map, 101);
```

---

## How pycparser Is Used (For Your Report)

Instead of building C strings manually, the visitor builds **real C AST nodes**:

```python
from pycparser import c_ast, c_generator

gen = c_generator.CGenerator()

# Build:  for (int i = 0; i < 5; i++) { printf(...); }
for_node = c_ast.For(
    init  = c_ast.Decl('i', ..., init=c_ast.Constant('int','0'), ...),
    cond  = c_ast.BinaryOp('<', c_ast.ID('i'), c_ast.Constant('int','5')),
    next  = c_ast.UnaryOp('p++', c_ast.ID('i')),
    stmt  = c_ast.Compound([...])
)

# Emit valid C:
print(gen.visit(for_node))
# → for (int i = 0; i < 5; i++) { ... }
```

This means the output is **always syntactically valid C** because pycparser's CGenerator handles all formatting, indentation, and punctuation correctly.
