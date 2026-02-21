# tests/test_new_j2c_features.py
# Tests for newly added Java->C features
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import java_to_c

def t(src): return java_to_c.translate_string(src)

# ── Math.* mapping ────────────────────────────────────────────────────────────

def test_math_sqrt():
    src = """public class Main { public static void main(String[] args) {
        double x = Math.sqrt(16.0);
    }}"""
    out = t(src)
    assert 'sqrt' in out
    assert '#include <math.h>' in out

def test_math_pow():
    src = """public class Main { public static void main(String[] args) {
        double x = Math.pow(2.0, 3.0);
    }}"""
    out = t(src)
    assert 'pow' in out
    assert '#include <math.h>' in out

def test_math_abs():
    src = """public class Main { public static void main(String[] args) {
        int x = Math.abs(-5);
    }}"""
    out = t(src)
    assert 'abs' in out

def test_math_sin_cos_tan():
    src = """public class Main { public static void main(String[] args) {
        double a = Math.sin(1.0);
        double b = Math.cos(1.0);
        double c = Math.tan(1.0);
    }}"""
    out = t(src)
    assert 'sin' in out
    assert 'cos' in out
    assert 'tan' in out

def test_math_ceil_floor():
    src = """public class Main { public static void main(String[] args) {
        double a = Math.ceil(2.3);
        double b = Math.floor(2.7);
    }}"""
    out = t(src)
    assert 'ceil' in out
    assert 'floor' in out

def test_math_log():
    src = """public class Main { public static void main(String[] args) {
        double a = Math.log(10.0);
        double b = Math.log10(100.0);
    }}"""
    out = t(src)
    assert 'log(' in out
    assert 'log10' in out

def test_math_pi():
    src = """public class Main { public static void main(String[] args) {
        double pi = Math.PI;
    }}"""
    out = t(src)
    assert 'M_PI' in out

def test_math_max_min():
    src = """public class Main { public static void main(String[] args) {
        double a = Math.max(1.0, 2.0);
        double b = Math.min(1.0, 2.0);
    }}"""
    out = t(src)
    assert 'fmax' in out
    assert 'fmin' in out

# ── String methods ────────────────────────────────────────────────────────────

def test_string_charat():
    src = """public class Main { public static void main(String[] args) {
        String s = "hello"; char c = s.charAt(0);
    }}"""
    out = t(src)
    assert 's[0]' in out

def test_string_indexof():
    src = """public class Main { public static void main(String[] args) {
        String s = "hello"; int i = s.indexOf("lo");
    }}"""
    out = t(src)
    assert 'strstr' in out

def test_string_contains():
    src = """public class Main { public static void main(String[] args) {
        String s = "hello";
        boolean b = s.contains("ell");
    }}"""
    out = t(src)
    assert 'strstr' in out
    assert 'NULL' in out

def test_string_isempty():
    src = """public class Main { public static void main(String[] args) {
        String s = "hello";
        boolean b = s.isEmpty();
    }}"""
    out = t(src)
    assert 'strlen' in out

def test_string_compareto():
    src = """public class Main { public static void main(String[] args) {
        String a = "abc"; String b = "def";
        int r = a.compareTo(b);
    }}"""
    out = t(src)
    assert 'strcmp' in out

# ── null handling ─────────────────────────────────────────────────────────────

def test_null_to_NULL():
    src = """public class Main { public static void main(String[] args) {
        String s = null;
    }}"""
    out = t(src)
    assert 'NULL' in out

# ── final -> const ────────────────────────────────────────────────────────────

def test_final_to_const():
    src = """public class Main { public static void main(String[] args) {
        final int MAX = 100;
    }}"""
    out = t(src)
    assert 'const' in out
    assert 'MAX' in out

# ── Integer.parseInt / atoi ────────────────────────────────────────────────────

def test_parseint():
    src = """public class Main { public static void main(String[] args) {
        int x = Integer.parseInt("42");
    }}"""
    out = t(src)
    assert 'atoi' in out

def test_parsedouble():
    src = """public class Main { public static void main(String[] args) {
        double x = Double.parseDouble("3.14");
    }}"""
    out = t(src)
    assert 'atof' in out

# ── ArrayList ─────────────────────────────────────────────────────────────────

def test_arraylist():
    src = """import java.util.ArrayList;
    public class Main { public static void main(String[] args) {
        ArrayList<Integer> list = new ArrayList<>();
        list.add(10);
        list.add(20);
        int sz = list.size();
    }}"""
    out = t(src)
    assert 'ArrayList' in out
    assert 'arraylist_create' in out
    assert 'arraylist_add' in out
    assert 'list.size' in out

# ── System.exit ───────────────────────────────────────────────────────────────

def test_system_exit():
    src = """public class Main { public static void main(String[] args) {
        System.exit(1);
    }}"""
    out = t(src)
    assert 'exit(1)' in out

# ── try/catch → body only ────────────────────────────────────────────────────

def test_try_catch():
    src = """public class Main { public static void main(String[] args) {
        try {
            int x = 5;
            System.out.println(x);
        } catch (Exception e) {
            System.out.println("error");
        }
    }}"""
    out = t(src)
    assert 'int x = 5' in out
    assert 'printf' in out

# ── enum ──────────────────────────────────────────────────────────────────────

# enum test requires javalang support; if not parsed, skip gracefully

# ── Static fields → globals ──────────────────────────────────────────────────

def test_static_field():
    src = """public class Main {
        static int counter = 0;
        public static void main(String[] args) {
            counter++;
        }
    }"""
    out = t(src)
    assert 'int counter = 0' in out

def test_static_final_field():
    src = """public class Main {
        static final int MAX = 100;
        public static void main(String[] args) {
            System.out.println(MAX);
        }
    }"""
    out = t(src)
    assert 'const' in out
    assert 'MAX' in out
    assert '100' in out
