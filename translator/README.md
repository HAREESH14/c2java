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

| Direction | Pass Rate | Compilable Features | Primary Failure Cases |
|-----------|-----------|--------------------|-----------------------|
| **C → Java** | 80% (8/10) | Math, loops, arrays, `switch` | Pointers, complex `struct` mapping |
| **C → C++** | 80% (8/10) | I/O, strings, standard libraries | Raw pointers requiring lifetime tracking |
| **Java → C** | 70% (7/10) | Control flow, basic math, recursion | High-level APIs (`String` manipulation), multi-dimensional arrays |
| **C++ → C** | 90% (9/10) | OOP (classes, inheritance, templates) | Deeply nested `enum class`, complex templates |
| **OVERALL** | **80% (32/40)** | | |

## Comparison with Existing Tools

| Feature | This Project | C2Rust | CxGo | Tangible |
|---------|--------------|--------|------|----------|
| **Supported Languages** | Java, C, C++ | C, Rust | C, Go | C#, Java, C++ |
| **Parsing Strategy** | Full AST | Full AST | Full AST | Regex / AST |
| **OOP Translation** | Advanced (Inheritance/vtable) | N/A | N/A | Standard |
| **Multi-file Batch** | Yes | Yes | Yes | Yes |
| **Research Focus** | High (Educational) | High (Safety) | Medium | Commercial |

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

## Limitations & Future Work

Honest constraints of the current implementation:

1. **Semantic Equivalence:** The tool guarantees syntactic translation and high compile rates, but runtime logic equivalence (e.g., matching C integer overflow behavior in Java) is outside the current scope.
2. **Memory Management:** `new`/`delete` and `malloc`/`free` are translated directly. It does not implement garbage collection logic when moving from Java to C, leading to potential memory leaks in translated C code.
3. **Complex C++ Templates:** Simple function templates are converted to C macros, but generic classes, SFINAE, and template metaprogramming are ignored.
4. **Header Resolution:** In batch mode, C/C++ header files are copied as-is rather than dynamically included across standard library paths.
5. **Standard Libraries:** Only a subset of `java.lang`, `<stdio.h>`, and `<iostream>` are mapped. Advanced standard library features (like threading or file streams) translate with limited fidelity.

## Testing

The project includes an automated suite of 236 unit tests covering language mappings.

```bash
uv run pytest tests/
```
