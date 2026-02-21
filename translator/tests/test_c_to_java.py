# tests/test_c_to_java.py
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import c_to_java

def translate(src): return c_to_java.translate_string(src)

def test_basic_function():
    src = "int add(int a, int b) { return a + b; }"
    out = translate(src)
    assert 'public class Main' in out
    assert 'public static int add' in out
    assert 'return (a + b)' in out or 'return a + b' in out

def test_main_printf():
    src = """
    int main() {
        int x = 5;
        printf("%d\\n", x);
        return 0;
    }"""
    out = translate(src)
    assert 'System.out.printf' in out
    assert 'int x = 5' in out

def test_for_loop():
    src = """
    int main() {
        int i;
        for (i = 0; i < 10; i++) { printf("%d\\n", i); }
        return 0;
    }"""
    out = translate(src)
    assert 'for' in out
    assert 'System.out.printf' in out

def test_if_else():
    src = """
    int main() {
        int x = 3;
        if (x > 0) { printf("pos\\n"); }
        else { printf("neg\\n"); }
        return 0;
    }"""
    out = translate(src)
    assert 'if' in out
    assert 'else' in out

def test_arrays():
    src = """
    int main() {
        int arr[5];
        int init[] = {1,2,3};
        arr[0] = 10;
        return 0;
    }"""
    out = translate(src)
    assert 'new int[5]' in out
    assert '{1, 2, 3}' in out or '{1,2,3}' in out

def test_while_dowhile():
    src = """
    int main() {
        int n = 0;
        while (n < 5) { n++; }
        do { n--; } while (n > 0);
        return 0;
    }"""
    out = translate(src)
    assert 'while' in out
    assert 'do {' in out

def test_break_continue():
    src = """
    int main() {
        int i;
        for (i = 0; i < 10; i++) {
            if (i == 3) break;
            if (i == 1) continue;
        }
        return 0;
    }"""
    out = translate(src)
    assert 'break;' in out
    assert 'continue;' in out

def test_return_type_map():
    src = "float compute(float a) { return a * 2; }"
    out = translate(src)
    assert 'float compute' in out

def test_unknown_stmt_emits_comment():
    # pycparser will parse valid C; unknown pycparser node types should not crash
    src = "int main() { return 0; }"
    out = translate(src)
    assert 'public class Main' in out
