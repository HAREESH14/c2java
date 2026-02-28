# Multi-Language Source-to-Source Transpiler (C ↔ Java ↔ C++)

A research-oriented source-to-source translation tool that supports **4 translation directions** using Abstract Syntax Trees (ASTs) rather than simple text replacement.

This project was built to explore the challenges of automated translation between procedural (C) and object-oriented (Java, C++) paradigms.

## Features & Translation Capabilities

Currently supports ~108 translation rules across 4 directions:

- **Java → C**: Translates classes to structs, methods to functions, handles basic I/O (`System.out.println` → `printf`), memory management (`new` → `malloc`), and arrays.
- **C → Java**: Translates structs to classes, functions to static methods, C libraries to Java equivalents (`<string.h>` → `java.lang.String`).
- **C → C++**: Upgrades C code to modern C++ (e.g., `printf` → `cout`, `malloc` → `new`, `struct` → `class`).
- **C++ → C**: Downgrades C++ to C, featuring complex OOP translations:
  - **Constructors/Destructors** → `_init()` and `_destroy()` functions
  - **Inheritance** → Struct composition (base class embedded as a field)
  - **Virtual Methods** → Function pointers in structs (vtable-like)
  - **Templates** → Preprocessor `#define` macros (for simple cases)

## Architecture

The translation pipeline relies on robust language parsers to build an AST, followed by custom visitor patterns to emit the target language.

```ascii
+----------------+      +---------------+      +-------------------+
|  Source Code   | ---> |    Parser     | ---> | Abstract Syntax   |
+----------------+      +---------------+      | Tree (AST)        |
     (C, Java,          (pycparser,            +-------------------+
      C++)               javalang,                       |
                         tree-sitter)                    |
                                                         v
+----------------+      +---------------+      +-------------------+
|  Target Code   | <--- | Code Emitter  | <--- |   AST Visitor     |
+----------------+      +---------------+      +-------------------+
```

## Accuracy Metrics

Evaluated on 40 diverse programs (10 per language) across all translation directions. A translation is considered a "PASS" only if the target output successfully compiles with standard compilers (`gcc`, `g++`, `javac`).

| Direction    | Pass Rate       | Compilable Features                   | Primary Failure Cases                                             |
| ------------ | --------------- | ------------------------------------- | ----------------------------------------------------------------- |
| **C → Java** | 80% (8/10)      | Math, loops, arrays, `switch`         | Pointers, complex `struct` mapping                                |
| **C → C++**  | 80% (8/10)      | I/O, strings, standard libraries      | Raw pointers requiring lifetime tracking                          |
| **Java → C** | 70% (7/10)      | Control flow, basic math, recursion   | High-level APIs (`String` manipulation), multi-dimensional arrays |
| **C++ → C**  | 90% (9/10)      | OOP (classes, inheritance, templates) | Deeply nested `enum class`, complex templates                     |
| **OVERALL**  | **80% (32/40)** |                                       |                                                                   |

## Comparison with Existing Tools

| Feature                 | This Project                  | C2Rust        | CxGo     | Tangible      |
| ----------------------- | ----------------------------- | ------------- | -------- | ------------- |
| **Supported Languages** | Java, C, C++                  | C, Rust       | C, Go    | C#, Java, C++ |
| **Parsing Strategy**    | Full AST                      | Full AST      | Full AST | Regex / AST   |
| **OOP Translation**     | Advanced (Inheritance/vtable) | N/A           | N/A      | Standard      |
| **Multi-file Batch**    | Yes                           | Yes           | Yes      | Yes           |
| **Research Focus**      | High (Educational)            | High (Safety) | Medium   | Commercial    |

## Installation & Usage

### Prerequisites

- Python 3.8+
- `uv` (Fast Python package installer)
- WSL (Windows Subsystem for Linux) with `gcc`, `g++`, and `javac` installed (for the `--verify` flag)

### Setup

```bash
# Provide python virtual environment
uv venv
# Activate it (Windows)
.venv\Scripts\activate
# Install dependencies
uv pip install pycparser javalang tree-sitter tree-sitter-cpp pytest
```

### CLI Usage

The tool supports translating single files, running built-in demos, and batch-processing entire folders.

```bash
# 1. Single File Translation
python src/main.py input.java           # Java -> C
python src/main.py input.c              # C -> Java
python src/main.py input.c --to cpp     # C -> C++
python src/main.py input.cpp            # C++ -> C

# 2. Batch Processing (Folder Mode)
python src/main.py samples/             # Translates all files in folder
python src/main.py samples/ --to cpp    # Translate all C files to C++
python src/main.py samples/ --output out/ # Save to specific directory

# 3. Verification & Debugging
python src/main.py input.java --verify  # Translate, then run target compiler
python src/main.py input.java --ast     # Print AST before translating
```

### Library Usage

You can embed translators into other Python projects:

```python
from translator.src import cpp_to_c

cpp_code = """
class Animal {
public:
    virtual void speak() {}
};
"""
c_code = cpp_to_c.translate_string(cpp_code)
print(c_code)
```

## Known Bugs & Limitations

Based on rigorous accuracy metrics, the translator successfully compiles **80%** of varied code samples. The remaining 20% fail due to the following known limitations of AST-based syntactical translation:

### 1. Pointer Dereferencing (C → Java)

Java lacks scalar pointers. While `malloc` successfully translates to `new int[]`, dereferencing fails:

- **C:** `*p = 42;`
- **Translated Java:** `p = 42;` (Compiler Error: incompatible types)
- _Workaround:_ Manual refactoring to `p[0] = 42;` or using object wrappers.

### 2. Struct Instantiation (C → Java)

C allows stack allocation of `structs`, which Java does not support without `new`:

- **C:** `struct Point p; p.x = 10;`
- **Translated Java:** `Point p; p.x = 10;` (Compiler Error: variable p might not have been initialized)
- _Workaround:_ Change C code to use pointers for structs or manually add `new Point()` in Java.

### 3. Array Length Mapping (Java → C)

Java's `.length` property on arrays does not translate directly because C arrays decay to pointers.

- **Java:** `arr.length`
- **Translated C:** `length` (Compiler Error: 'length' undeclared)
- _Workaround:_ Pass array sizes explicitly in C or use a macro like `sizeof(arr)/sizeof(arr[0])` for static arrays.

### 4. C++ Scoped Enums (C++ → C)

C++ `enum class` requires scope resolution (`Color::RED`), which is invalid in standard C.

- **C++:** `Color c = Color::RED;`
- **Translated C:** `Color c = Color::RED;` (Compiler Error: expected expression before 'Color')
- _Workaround:_ Use traditional C-style enums (`enum Color { RED }; Color c = RED;`).

### 5. Math Library Linking (Java → C)

Translating `Math.sqrt()` to `sqrt()` in C works syntactically, but compiling the resulting C code requires explicitly linking the math library (`-lm` flag). While not a strict translation bug, it causes automated compile steps to fail with "undefined reference to `sqrt`".

## Testing

The project includes an automated suite of 236 unit tests covering language mappings.

```bash
uv run pytest tests/
```
