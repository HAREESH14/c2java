# tests/test_java_to_c.py
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import java_to_c

def translate(src): return java_to_c.translate_string(src)

def test_variables_and_if():
    src = """public class Main {
        public static void main(String[] args) {
            int x = 10;
            float f = 3.14f;
            if (x > 5) { System.out.println(x); } else { System.out.println(0); }
        }
    }"""
    out = translate(src)
    assert 'int x = 10' in out
    assert 'printf' in out
    assert 'if' in out

def test_for_while_dowhile():
    src = """public class Main {
        public static void main(String[] args) {
            for (int i = 0; i < 5; i++) { System.out.println(i); }
            int n = 0;
            while (n < 3) { n += 1; }
            do { n -= 1; } while (n > 0);
        }
    }"""
    out = translate(src)
    assert 'for' in out
    assert 'while' in out
    assert 'do' in out

def test_arrays():
    src = """public class Main {
        public static void main(String[] args) {
            int[] arr = new int[5];
            int[] init = {1,2,3};
            arr[0] = 99;
        }
    }"""
    out = translate(src)
    assert 'int arr[5]' in out
    assert '{1, 2, 3}' in out or '{1,2,3}' in out

def test_functions_and_forward_decl():
    src = """public class Main {
        public static int add(int a, int b) { return a + b; }
        public static void main(String[] args) {
            int r = add(3, 4);
            System.out.println(r);
        }
    }"""
    out = translate(src)
    assert 'int add(int a, int b);' in out   # forward decl
    assert 'return a + b' in out

def test_break_continue_switch():
    src = """public class Main {
        public static void main(String[] args) {
            for (int i=0;i<10;i++) { if(i==3) break; if(i==1) continue; }
            int d = 2;
            switch(d){case 1: System.out.println(1); break; default: System.out.println(0); break;}
        }
    }"""
    out = translate(src)
    assert 'break' in out
    assert 'continue' in out
    assert 'switch' in out

def test_hashmap():
    src = """import java.util.HashMap;
    public class Main {
        public static void main(String[] args) {
            HashMap<Integer,Integer> m = new HashMap<>();
            m.put(1, 100);
            int v = m.get(1);
            if (m.containsKey(1)) System.out.println(v);
        }
    }"""
    out = translate(src)
    assert 'HashMap' in out
    assert 'hashmap_put' in out
    assert 'hashmap_get' in out

def test_foreach_no_crash():
    src = """public class Main {
        public static void main(String[] args) {
            int[] a = {1,2,3};
            for (int x : a) System.out.println(x);
        }
    }"""
    out = translate(src)
    assert 'for' in out     # for-each emitted as C for loop

def test_compound_assign():
    src = """public class Main {
        public static void main(String[] args) {
            int x = 10;
            x += 5; x -= 2; x *= 3; x /= 4;
            System.out.println(x);
        }
    }"""
    out = translate(src)
    assert '+=' in out
    assert '-=' in out
