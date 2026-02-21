# tests/test_c_to_java_extended.py
# Extended tests for C -> Java translator covering edge cases
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import c_to_java

def t(src): return c_to_java.translate_string(src)

# ── Type mapping ──────────────────────────────────────────────────────────────

def test_all_types():
    src = """int main() {
        int a = 1; float b = 2.0f; double c = 3.0;
        char d; long e = 100; short f = 5; return 0;
    }"""
    out = t(src)
    assert 'int a = 1' in out
    assert 'float b' in out
    assert 'double c' in out
    assert 'char d' in out
    assert 'long e' in out
    assert 'short f' in out

def test_char_array_to_string():
    src = 'int main() { char name[] = "Hello"; return 0; }'
    out = t(src)
    assert 'String name' in out

def test_char_ptr_to_string():
    src = 'int main() { char *msg = "world"; return 0; }'
    out = t(src)
    assert 'String msg' in out

# ── Operators ─────────────────────────────────────────────────────────────────

def test_prefix_postfix():
    src = "int main() { int x = 5; x++; ++x; x--; --x; return 0; }"
    out = t(src)
    assert 'x++' in out
    assert '++x' in out
    assert 'x--' in out
    assert '--x' in out

def test_compound_assigns():
    src = "int main() { int x = 10; x += 5; x -= 2; x *= 3; x /= 4; return 0; }"
    out = t(src)
    for op in ['+=', '-=', '*=', '/=']:
        assert op in out

def test_ternary():
    src = "int main() { int x = 10; int y = x > 5 ? 1 : 0; return 0; }"
    out = t(src)
    assert '?' in out and ':' in out

# ── Control flow ──────────────────────────────────────────────────────────────

def test_nested_if():
    src = """int main() {
        int x = 5;
        if (x > 10) { printf("big\\n"); }
        else if (x > 5) { printf("mid\\n"); }
        else { printf("small\\n"); }
        return 0;
    }"""
    out = t(src)
    assert 'if' in out
    assert 'else if' in out
    assert 'else {' in out

def test_for_with_init_decl():
    src = """int main() {
        int i;
        for (i = 0; i < 10; i++) { printf("%d\\n", i); }
        return 0;
    }"""
    out = t(src)
    assert 'for' in out

def test_while():
    src = "int main() { int n = 10; while (n > 0) { n--; } return 0; }"
    out = t(src)
    assert 'while' in out

def test_do_while():
    src = "int main() { int n = 0; do { n++; } while(n < 5); return 0; }"
    out = t(src)
    assert 'do {' in out
    assert 'while' in out

def test_switch():
    src = """int main() {
        int x = 2;
        switch(x) {
            case 1: printf("one\\n"); break;
            case 2: printf("two\\n"); break;
            default: printf("other\\n"); break;
        }
        return 0;
    }"""
    out = t(src)
    assert 'switch' in out
    assert 'case 1' in out
    assert 'case 2' in out
    assert 'default' in out

def test_break_continue():
    src = """int main() {
        int i;
        for (i = 0; i < 20; i++) {
            if (i % 2 == 0) continue;
            if (i > 9) break;
        }
        return 0;
    }"""
    out = t(src)
    assert 'break;' in out
    assert 'continue;' in out

# ── Arrays ────────────────────────────────────────────────────────────────────

def test_array_new():
    src = "int main() { int arr[10]; return 0; }"
    out = t(src)
    assert 'new int[10]' in out

def test_array_init():
    src = "int main() { int arr[] = {1, 2, 3}; return 0; }"
    out = t(src)
    assert '{1, 2, 3}' in out or '{1,2,3}' in out

# ── Functions ─────────────────────────────────────────────────────────────────

def test_non_main_function():
    src = "int add(int a, int b) { return a + b; }"
    out = t(src)
    assert 'public static int add(int a, int b)' in out

def test_void_function():
    src = "void greet() { printf(\"hi\\n\"); }"
    out = t(src)
    assert 'public static void greet' in out

def test_main_returns_void():
    src = "int main() { return 0; }"
    out = t(src)
    assert 'public static void main(String[] args)' in out

def test_main_return_0_stripped():
    src = "int main() { printf(\"hi\\n\"); return 0; }"
    out = t(src)
    assert 'return;' in out or 'return 0' not in out

# ── IO ────────────────────────────────────────────────────────────────────────

def test_printf_to_sysout():
    src = 'int main() { printf("hello %d\\n", 42); return 0; }'
    out = t(src)
    assert 'System.out.printf' in out

def test_scanf_int():
    src = 'int main() { int x; scanf("%d", &x); return 0; }'
    out = t(src)
    assert 'Scanner' in out
    assert 'sc.nextInt()' in out

def test_scanf_float():
    src = 'int main() { float f; scanf("%f", &f); return 0; }'
    out = t(src)
    assert 'sc.nextFloat()' in out

# ── String/Math library ──────────────────────────────────────────────────────

def test_strlen_to_length():
    src = 'int main() { char *s = "hi"; int l = strlen(s); return 0; }'
    out = t(src)
    assert '.length()' in out

def test_strcmp_to_compareto():
    src = 'int main() { char *a = "hi"; char *b = "bye"; int r = strcmp(a, b); return 0; }'
    out = t(src)
    assert '.compareTo(' in out

def test_sqrt_to_math():
    src = 'int main() { double x = sqrt(16.0); return 0; }'
    out = t(src)
    assert 'Math.sqrt' in out

def test_pow_to_math():
    src = 'int main() { double x = pow(2.0, 3.0); return 0; }'
    out = t(src)
    assert 'Math.pow' in out

# ── Error recovery ───────────────────────────────────────────────────────────

def test_class_wrapper():
    src = "int main() { return 0; }"
    out = t(src)
    assert 'public class Main' in out

def test_empty_main():
    src = "int main() { return 0; }"
    out = t(src)
    assert 'public static void main' in out

def test_multiple_functions():
    src = """
    int fact(int n) { if (n <= 1) return 1; return n * fact(n - 1); }
    int main() { int r = fact(5); printf("%d\\n", r); return 0; }
    """
    out = t(src)
    assert 'public static int fact' in out
    assert 'fact(5)' in out
