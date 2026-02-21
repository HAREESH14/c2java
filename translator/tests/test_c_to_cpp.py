# tests/test_c_to_cpp.py
# Tests for C -> C++ translation using pycparser AST
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import c_to_cpp

def t(src): return c_to_cpp.translate_string(src)

# ── Core features ─────────────────────────────────────────────────────────────

def test_basic_main():
    src = "int main() { return 0; }"
    out = t(src)
    assert 'int main' in out
    assert 'return 0;' in out

def test_variables():
    src = "int main() { int a = 10; float b = 3.14f; return 0; }"
    out = t(src)
    assert 'int a = 10;' in out
    assert 'float b = 3.14f;' in out

def test_includes():
    out = t("int main() { return 0; }")
    assert '#include <iostream>' in out

# ── printf -> cout ──────────────────────────────────────────────────────────

def test_printf_string():
    src = 'int main() { printf("hello\\n"); return 0; }'
    out = t(src)
    assert 'cout' in out

def test_printf_variable():
    src = 'int main() { int x = 5; printf("x=%d\\n", x); return 0; }'
    out = t(src)
    assert 'cout' in out

def test_puts_to_cout():
    src = 'int main() { puts("hello"); return 0; }'
    out = t(src)
    assert 'cout' in out
    assert 'endl' in out

# ── scanf -> cin ──────────────────────────────────────────────────────────

def test_scanf_to_cin():
    src = 'int main() { int x; scanf("%d", &x); return 0; }'
    out = t(src)
    assert 'cin' in out

# ── strings ────────────────────────────────────────────────────────────────

def test_char_ptr_to_string():
    src = 'int main() { char *s = "hello"; return 0; }'
    out = t(src)
    assert 'string' in out

def test_char_array_to_string():
    src = 'int main() { char name[] = "hello"; return 0; }'
    out = t(src)
    assert 'string' in out

def test_strlen_to_length():
    src = 'int main() { char *s = "hi"; int n = strlen(s); return 0; }'
    out = t(src)
    assert '.length()' in out

def test_strcmp_to_compare():
    src = 'int main() { char *a = "hi"; char *b = "ho"; int r = strcmp(a, b); return 0; }'
    out = t(src)
    assert '.compare(' in out

# ── malloc/free -> new/delete ──────────────────────────────────────────────

def test_malloc_to_new():
    src = "int main() { int *arr = malloc(40); return 0; }"
    out = t(src)
    assert 'new int' in out

def test_free_to_delete():
    src = "int main() { int *p; free(p); return 0; }"
    out = t(src)
    assert 'delete' in out

# ── struct -> class ──────────────────────────────────────────────────────────

def test_struct_to_class():
    src = "struct Point { int x; int y; }; int main() { return 0; }"
    out = t(src)
    assert 'class Point' in out
    assert 'public:' in out

# ── enum ──────────────────────────────────────────────────────────────────────

def test_enum():
    src = "enum Color { RED, GREEN, BLUE }; int main() { return 0; }"
    out = t(src)
    assert 'enum class Color' in out
    assert 'RED' in out

# ── const ─────────────────────────────────────────────────────────────────────

def test_const():
    src = "int main() { const int MAX = 100; return 0; }"
    out = t(src)
    assert 'const' in out
    assert '100' in out

# ── NULL -> nullptr ───────────────────────────────────────────────────────────

def test_null_to_nullptr():
    src = "int main() { int *p = NULL; return 0; }"
    out = t(src)
    assert 'nullptr' in out

# ── casts ─────────────────────────────────────────────────────────────────────

def test_cast():
    src = "int main() { float x = 3.14f; int y = (int)x; return 0; }"
    out = t(src)
    assert 'static_cast<int>' in out or '(int)' in out

# ── control flow ──────────────────────────────────────────────────────────────

def test_if_else():
    src = "int main() { int x = 5; if (x > 3) { x = 1; } else { x = 2; } return 0; }"
    out = t(src)
    assert 'if' in out
    assert 'else' in out

def test_for_loop():
    src = "int main() { int i; for (i = 0; i < 5; i++) { } return 0; }"
    out = t(src)
    assert 'for' in out

def test_while_loop():
    src = "int main() { int n = 10; while (n > 0) { n--; } return 0; }"
    out = t(src)
    assert 'while' in out

def test_switch():
    src = "int main() { int x = 1; switch (x) { case 1: break; default: break; } return 0; }"
    out = t(src)
    assert 'switch' in out
    assert 'case 1' in out

# ── exit -> exit ──────────────────────────────────────────────────────────────

def test_exit():
    src = "int main() { exit(0); return 0; }"
    out = t(src)
    assert 'exit(0)' in out

# ── math functions stay ──────────────────────────────────────────────────────

def test_sqrt():
    src = "int main() { double x = sqrt(4.0); return 0; }"
    out = t(src)
    assert 'sqrt' in out
    assert 'cmath' in out

# ── atoi -> stoi ──────────────────────────────────────────────────────────────

def test_atoi_to_stoi():
    src = 'int main() { char *s = "42"; int x = atoi(s); return 0; }'
    out = t(src)
    assert 'stoi' in out

# ── function declaration ──────────────────────────────────────────────────────

def test_function():
    src = "int add(int a, int b) { return a + b; } int main() { int r = add(1, 2); return 0; }"
    out = t(src)
    assert 'int add(int a, int b)' in out
