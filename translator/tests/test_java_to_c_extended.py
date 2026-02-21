# tests/test_java_to_c_extended.py
# Extended tests covering edge cases and detailed output verification
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import java_to_c

def t(src): return java_to_c.translate_string(src)

# ── Type mapping ──────────────────────────────────────────────────────────────

def test_all_primitive_types():
    src = """public class Main { public static void main(String[] args) {
        int a = 1; float b = 2.0f; double c = 3.0;
        char d = 'x'; boolean e = true; long f = 100;
        short g = 5;
    }}"""
    out = t(src)
    assert 'int a = 1' in out
    assert 'float b = 2.0' in out
    assert 'double c = 3.0' in out
    assert "char d = 'x'" in out
    assert 'int e = 1' in out      # boolean -> int 1
    assert 'long f = 100' in out
    assert 'short g = 5' in out

def test_string_type():
    src = """public class Main { public static void main(String[] args) {
        String msg = "hello";
    }}"""
    out = t(src)
    assert 'char*' in out or 'char *' in out

# ── Operators ─────────────────────────────────────────────────────────────────

def test_prefix_postfix():
    src = """public class Main { public static void main(String[] args) {
        int x = 5; x++; ++x; x--; --x;
    }}"""
    out = t(src)
    assert 'x++' in out
    assert '++x' in out
    assert 'x--' in out
    assert '--x' in out

def test_ternary():
    src = """public class Main { public static void main(String[] args) {
        int x = 10; int y = x > 5 ? 1 : 0;
    }}"""
    out = t(src)
    assert '?' in out
    assert ':' in out

def test_compound_assignments():
    src = """public class Main { public static void main(String[] args) {
        int x = 10; x += 5; x -= 2; x *= 3; x /= 4;
    }}"""
    out = t(src)
    for op in ['+=', '-=', '*=', '/=']:
        assert op in out, f"Missing {op}"

# ── Control flow ──────────────────────────────────────────────────────────────

def test_nested_if_else():
    src = """public class Main { public static void main(String[] args) {
        int x = 10;
        if (x > 20) { System.out.println(1); }
        else if (x > 10) { System.out.println(2); }
        else if (x > 5) { System.out.println(3); }
        else { System.out.println(4); }
    }}"""
    out = t(src)
    assert out.count('if') >= 3
    assert out.count('else') >= 2

def test_switch_with_default():
    src = """public class Main { public static void main(String[] args) {
        int x = 2;
        switch (x) {
            case 1: System.out.println(1); break;
            case 2: System.out.println(2); break;
            case 3: System.out.println(3); break;
            default: System.out.println(0); break;
        }
    }}"""
    out = t(src)
    assert 'case 1' in out
    assert 'case 2' in out
    assert 'case 3' in out
    assert 'default' in out

def test_break_continue_in_loop():
    src = """public class Main { public static void main(String[] args) {
        for (int i = 0; i < 100; i++) {
            if (i % 2 == 0) continue;
            if (i > 10) break;
            System.out.println(i);
        }
    }}"""
    out = t(src)
    assert 'continue' in out
    assert 'break' in out

def test_while_loop():
    src = """public class Main { public static void main(String[] args) {
        int n = 100; while (n > 0) { n -= 7; }
    }}"""
    out = t(src)
    assert 'while' in out
    assert 'n > 0' in out or '(n > 0)' in out

def test_do_while_loop():
    src = """public class Main { public static void main(String[] args) {
        int n = 0; do { n++; } while (n < 10);
    }}"""
    out = t(src)
    assert 'do' in out
    assert 'while' in out

# ── Arrays ────────────────────────────────────────────────────────────────────

def test_2d_array():
    src = """public class Main { public static void main(String[] args) {
        int[][] grid = new int[3][4];
        grid[0][1] = 5;
    }}"""
    out = t(src)
    assert 'grid[3][4]' in out or 'int grid[3][4]' in out

def test_array_with_initializer():
    src = """public class Main { public static void main(String[] args) {
        int[] primes = {2, 3, 5, 7, 11, 13};
    }}"""
    out = t(src)
    assert '2' in out and '13' in out

# ── Functions ─────────────────────────────────────────────────────────────────

def test_multiple_functions():
    src = """public class Main {
        public static int square(int x) { return x * x; }
        public static int cube(int x) { return x * x * x; }
        public static void main(String[] args) {
            System.out.println(square(3));
            System.out.println(cube(2));
        }
    }"""
    out = t(src)
    assert 'int square(int x);' in out   # forward decl
    assert 'int cube(int x);' in out     # forward decl
    assert 'square(3)' in out
    assert 'cube(2)' in out

def test_void_function():
    src = """public class Main {
        public static void greet() { System.out.println("hi"); }
        public static void main(String[] args) { greet(); }
    }"""
    out = t(src)
    assert 'void greet()' in out

# ── IO ────────────────────────────────────────────────────────────────────────

def test_println_string():
    src = """public class Main { public static void main(String[] args) {
        System.out.println("hello world");
    }}"""
    out = t(src)
    assert 'printf' in out
    assert 'hello world' in out

def test_printf_format():
    src = """public class Main { public static void main(String[] args) {
        int x = 42;
        System.out.printf("value = %d%n", x);
    }}"""
    out = t(src)
    assert 'printf' in out
    assert '%d' in out

def test_println_concat():
    src = """public class Main { public static void main(String[] args) {
        int x = 5;
        System.out.println("x = " + x);
    }}"""
    out = t(src)
    assert 'printf' in out
    assert 'x = ' in out

# ── String operations ────────────────────────────────────────────────────────

def test_string_equals():
    src = """public class Main { public static void main(String[] args) {
        String a = "hello"; String b = "hello";
        if (a.equals(b)) System.out.println("same");
    }}"""
    out = t(src)
    assert 'strcmp' in out
    assert 'string.h' in out

def test_string_length():
    src = """public class Main { public static void main(String[] args) {
        String s = "test"; int len = s.length();
    }}"""
    out = t(src)
    assert 'strlen' in out

# ── HashMap ───────────────────────────────────────────────────────────────────

def test_hashmap_full():
    src = """import java.util.HashMap;
    public class Main { public static void main(String[] args) {
        HashMap<Integer, Integer> m = new HashMap<>();
        m.put(1, 10);
        m.put(2, 20);
        int val = m.get(1);
        boolean has = m.containsKey(2);
    }}"""
    out = t(src)
    assert 'HashMap' in out
    assert 'hashmap_create' in out
    assert 'hashmap_put' in out
    assert 'hashmap_get' in out
    assert 'hashmap_contains' in out

# ── Error recovery ────────────────────────────────────────────────────────────

def test_no_crash_on_empty_main():
    src = """public class Main { public static void main(String[] args) {} }"""
    out = t(src)
    assert 'int main' in out
    assert 'return 0' in out

def test_includes_always_present():
    src = """public class Main { public static void main(String[] args) {
        int x = 1;
    }}"""
    out = t(src)
    assert '#include <stdio.h>' in out
    assert '#include <stdlib.h>' in out
