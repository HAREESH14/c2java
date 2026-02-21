# tests/test_new_c2j_features.py
# Tests for newly added C->Java features
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import c_to_java

def t(src): return c_to_java.translate_string(src)

# ── const → final ─────────────────────────────────────────────────────────────

def test_const_to_final():
    src = "int main() { const int MAX = 100; return 0; }"
    out = t(src)
    assert 'final' in out
    assert 'MAX' in out

def test_const_double():
    src = "int main() { const double PI = 3.14159; return 0; }"
    out = t(src)
    assert 'final' in out
    assert 'PI' in out

# ── NULL → null ───────────────────────────────────────────────────────────────

def test_null_literal():
    src = "int main() { char *p = NULL; return 0; }"
    out = t(src)
    assert 'null' in out

# ── exit → System.exit ───────────────────────────────────────────────────────

def test_exit():
    src = "int main() { exit(1); return 0; }"
    out = t(src)
    assert 'System.exit(1)' in out

# ── puts → println ───────────────────────────────────────────────────────────

def test_puts():
    src = 'int main() { puts("hello"); return 0; }'
    out = t(src)
    assert 'System.out.println' in out

# ── sizeof ────────────────────────────────────────────────────────────────────

def test_sizeof_constant():
    src = "int main() { int x = sizeof(int); return 0; }"
    out = t(src)
    assert '4' in out

# ── M_PI / M_E / INT_MAX ─────────────────────────────────────────────────────

def test_m_pi():
    src = "int main() { double pi = M_PI; return 0; }"
    out = t(src)
    assert 'Math.PI' in out

def test_int_max():
    src = "int main() { int x = INT_MAX; return 0; }"
    out = t(src)
    assert 'Integer.MAX_VALUE' in out

# ── struct → class ────────────────────────────────────────────────────────────

def test_struct_to_class():
    src = """
    struct Point { int x; int y; };
    int main() { return 0; }
    """
    out = t(src)
    assert 'static class Point' in out
    assert 'int x;' in out
    assert 'int y;' in out

def test_struct_with_array():
    src = """
    struct Data { int values[10]; int count; };
    int main() { return 0; }
    """
    out = t(src)
    assert 'static class Data' in out
    assert 'int[] values' in out

# ── enum ──────────────────────────────────────────────────────────────────────

def test_enum_simple():
    src = """
    enum Color { RED, GREEN, BLUE };
    int main() { return 0; }
    """
    out = t(src)
    assert 'RED' in out
    assert 'GREEN' in out
    assert 'BLUE' in out

def test_enum_with_values():
    src = """
    enum Status { OK = 0, ERROR = 1, PENDING = 2 };
    int main() { return 0; }
    """
    out = t(src)
    assert 'OK' in out
    assert 'ERROR' in out
    assert 'PENDING' in out

# ── 2D arrays ─────────────────────────────────────────────────────────────────

def test_2d_array():
    src = "int main() { int grid[3][4]; return 0; }"
    out = t(src)
    assert 'int[][]' in out or 'new int[3][4]' in out

# ── malloc → new ──────────────────────────────────────────────────────────────

def test_malloc_to_new():
    src = "int main() { int *arr = malloc(40); return 0; }"
    out = t(src)
    assert 'new int' in out

# ── free → GC comment ────────────────────────────────────────────────────────

def test_free_to_comment():
    src = "int main() { int *arr; free(arr); return 0; }"
    out = t(src)
    assert 'GC' in out or 'free' in out

# ── putchar ───────────────────────────────────────────────────────────────────

def test_putchar():
    src = "int main() { putchar('A'); return 0; }"
    out = t(src)
    assert 'System.out.print' in out

# ── srand → comment ──────────────────────────────────────────────────────────

def test_srand_comment():
    src = "int main() { srand(42); return 0; }"
    out = t(src)
    assert 'srand' in out

# ── Additional math functions ─────────────────────────────────────────────────

def test_exp():
    src = "int main() { double x = exp(1.0); return 0; }"
    out = t(src)
    assert 'Math.exp' in out

def test_atan2():
    src = "int main() { double x = atan2(1.0, 2.0); return 0; }"
    out = t(src)
    assert 'Math.atan2' in out

def test_fmax_fmin():
    src = "int main() { double a = fmax(1.0, 2.0); double b = fmin(1.0, 2.0); return 0; }"
    out = t(src)
    assert 'Math.max' in out
    assert 'Math.min' in out

# ── char* / char[] → String ──────────────────────────────────────────────────

def test_char_ptr_string():
    src = 'int main() { char *msg = "hello"; return 0; }'
    out = t(src)
    assert 'String msg' in out

def test_char_array_string():
    src = 'int main() { char name[] = "world"; return 0; }'
    out = t(src)
    assert 'String name' in out

# ── multiple return types ────────────────────────────────────────────────────

def test_float_return():
    src = "float avg(float a, float b) { return (a + b) / 2.0f; }"
    out = t(src)
    assert 'public static float avg' in out

def test_double_return():
    src = "double square(double x) { return x * x; }"
    out = t(src)
    assert 'public static double square' in out

def test_char_return():
    src = "char grade(int score) { if (score > 90) return 'A'; return 'B'; }"
    out = t(src)
    assert 'public static char grade' in out
