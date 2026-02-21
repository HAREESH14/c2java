# C ↔ Java Translator

A bidirectional source-code translator between C and Java, built with:

- **[javalang](https://github.com/c2jai/javalang)** — Java parser (AST)
- **[pycparser](https://github.com/eliben/pycparser)** — C parser (AST)

## Project Structure

```
translator/
├── src/
│   ├── main.py        CLI entry point (auto-detects .java or .c)
│   ├── java_to_c.py   Java → C  (javalang AST + pycparser C backend)
│   ├── c_to_java.py   C → Java  (pycparser AST + string emitter)
│   └── verify.py      WSL gcc compilation check
├── tests/
│   ├── test_java_to_c.py   (8 tests)
│   └── test_c_to_java.py   (9 tests)
├── samples/
│   ├── fibonacci.java
│   └── calculator.c
└── pyproject.toml     (uv project)
```

## Usage

```bash
cd translator

# Java -> C (with WSL gcc compile check)
uv run python src/main.py samples/fibonacci.java --verify

# C -> Java
uv run python src/main.py samples/calculator.c

# Show AST while translating
uv run python src/main.py input.java --ast

# Built-in demo (both directions)
uv run python src/main.py --demo

# Run all 17 tests
uv run pytest tests/ -v
```

## Supported Translations

### Java → C

| Feature                          | Example                                                      |
| -------------------------------- | ------------------------------------------------------------ |
| Primitive types                  | `int`, `float`, `double`, `char`, `boolean`, `long`, `short` |
| Variables & arrays (1D/2D)       | `int[] a = new int[5];` → `int a[5];`                        |
| if / else if / else              | ✅                                                           |
| for / while / do-while           | ✅                                                           |
| for-each                         | `for (int x : arr)` → C index loop                           |
| break / continue                 | ✅                                                           |
| switch / case / default          | ✅                                                           |
| Functions + forward declarations | ✅                                                           |
| Compound assignments             | `x += 5; x *= 2;` ✅                                         |
| `System.out.println` / `printf`  | → `printf(...)`                                              |
| `String.equals()` / `.length()`  | → `strcmp` / `strlen`                                        |
| `HashMap<K,V>`                   | → struct simulation                                          |
| Ternary `? :`                    | ✅                                                           |

### C → Java

| Feature                     | Example                                 |
| --------------------------- | --------------------------------------- |
| Functions                   | → `public static` methods               |
| Arrays                      | `int arr[5]` → `int[] arr = new int[5]` |
| `printf`                    | → `System.out.printf`                   |
| `scanf`                     | → `Scanner sc.nextInt()` etc.           |
| `Math.*`                    | `sqrt`, `pow`, `sin`, `cos`…            |
| `strlen` / `strcmp`         | → `s.length()` / `s.compareTo()`        |
| `Integer.parseInt` / `atoi` | ✅                                      |
| switch / case / default     | ✅                                      |
| break / continue            | ✅                                      |

## Test Results

```
17 passed in 0.11s
```

WSL `gcc -Wall` compilation: **PASS** on all generated C files.
