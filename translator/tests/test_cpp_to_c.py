# tests/test_cpp_to_c.py
# Tests for C++ -> C translation using tree-sitter AST
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import cpp_to_c

def t(src): return cpp_to_c.translate_string(src)

# ── Core features ─────────────────────────────────────────────────────────────

def test_basic_main():
    src = "int main() { return 0; }"
    out = t(src)
    assert 'int main' in out
    assert 'return 0;' in out

def test_variables():
    src = "int main() { int a = 10; double b = 3.14; return 0; }"
    out = t(src)
    assert 'int a = 10;' in out
    assert 'double b = 3.14;' in out

def test_includes_translated():
    src = '#include <iostream>\nint main() { return 0; }'
    out = t(src)
    assert '#include <stdio.h>' in out

def test_using_namespace_stripped():
    src = '#include <iostream>\nusing namespace std;\nint main() { return 0; }'
    out = t(src)
    assert 'using namespace' not in out

# ── cout -> printf ───────────────────────────────────────────────────────────

def test_cout_string():
    src = '#include <iostream>\nusing namespace std;\nint main() { cout << "hello" << endl; return 0; }'
    out = t(src)
    assert 'printf("hello\\n");' in out

def test_cout_variable():
    src = '#include <iostream>\nusing namespace std;\nint main() { int x = 5; cout << "x=" << x << endl; return 0; }'
    out = t(src)
    assert 'printf' in out

def test_cout_no_endl():
    src = '#include <iostream>\nusing namespace std;\nint main() { cout << "hi"; return 0; }'
    out = t(src)
    assert 'printf("hi");' in out

# ── cin -> scanf ──────────────────────────────────────────────────────────────

def test_cin_to_scanf():
    src = '#include <iostream>\nusing namespace std;\nint main() { int x; cin >> x; return 0; }'
    out = t(src)
    assert 'scanf("%d", &x);' in out

def test_cin_multiple():
    src = '#include <iostream>\nusing namespace std;\nint main() { int a, b; cin >> a >> b; return 0; }'
    out = t(src)
    assert 'scanf' in out
    assert '&a' in out
    assert '&b' in out

# ── bool -> int, true/false -> 1/0 ──────────────────────────────────────────

def test_bool_to_int():
    src = "int main() { bool flag = true; return 0; }"
    out = t(src)
    assert 'int flag = 1;' in out

def test_false_to_zero():
    src = "int main() { bool b = false; return 0; }"
    out = t(src)
    assert 'int b = 0;' in out

# ── nullptr -> NULL ──────────────────────────────────────────────────────────

def test_nullptr_to_null():
    src = "int main() { int* p = nullptr; return 0; }"
    out = t(src)
    assert 'NULL' in out

# ── new/delete -> malloc/free ─────────────────────────────────────────────────

def test_new_to_malloc():
    src = "int main() { int* arr = new int[10]; return 0; }"
    out = t(src)
    assert 'malloc' in out

def test_delete_to_free():
    src = "int main() { int* arr = new int[5]; delete[] arr; return 0; }"
    out = t(src)
    assert 'free(arr)' in out

# ── class -> struct ──────────────────────────────────────────────────────────

def test_class_to_struct():
    src = """
    class Point {
    public:
        int x;
        int y;
    };
    int main() { return 0; }
    """
    out = t(src)
    assert 'typedef struct' in out
    assert 'Point;' in out
    assert 'int x;' in out
    assert 'int y;' in out
    # public: should be removed
    assert 'public:' not in out

# ── string -> char* ──────────────────────────────────────────────────────────

def test_string_to_char():
    src = '#include <string>\nusing namespace std;\nint main() { string name = "hello"; return 0; }'
    out = t(src)
    assert 'char*' in out

# ── string methods -> C functions ────────────────────────────────────────────

def test_length_to_strlen():
    src = '#include <string>\nusing namespace std;\nint main() { string s = "hi"; int n = s.length(); return 0; }'
    out = t(src)
    assert 'strlen(s)' in out

def test_compare_to_strcmp():
    src = '#include <string>\nusing namespace std;\nint main() { string a = "hi"; string b = "ho"; int r = a.compare(b); return 0; }'
    out = t(src)
    assert 'strcmp(a, b)' in out

# ── stoi/stod -> atoi/atof ──────────────────────────────────────────────────

def test_stoi_to_atoi():
    src = '#include <string>\nusing namespace std;\nint main() { string s = "42"; int x = stoi(s); return 0; }'
    out = t(src)
    assert 'atoi(s)' in out

def test_stod_to_atof():
    src = '#include <string>\nusing namespace std;\nint main() { string s = "3.14"; double x = stod(s); return 0; }'
    out = t(src)
    assert 'atof(s)' in out

# ── static_cast -> C cast ────────────────────────────────────────────────────

def test_static_cast():
    src = "int main() { double x = 3.14; int y = static_cast<int>(x); return 0; }"
    out = t(src)
    assert '(int)(x)' in out

# ── control flow ──────────────────────────────────────────────────────────────

def test_if_else():
    src = "int main() { int x = 5; if (x > 3) { x = 1; } else { x = 2; } return 0; }"
    out = t(src)
    assert 'if' in out
    assert 'else' in out

def test_for_loop():
    src = "int main() { for (int i = 0; i < 5; i++) { } return 0; }"
    out = t(src)
    assert 'for' in out

def test_while_loop():
    src = "int main() { int n = 10; while (n > 0) { n--; } return 0; }"
    out = t(src)
    assert 'while' in out

def test_do_while():
    src = "int main() { int n = 0; do { n++; } while (n < 5); return 0; }"
    out = t(src)
    assert 'do {' in out
    assert 'while' in out

def test_switch():
    src = """
    #include <iostream>
    using namespace std;
    int main() {
        int x = 1;
        switch (x) {
            case 1: cout << "one" << endl; break;
            case 2: cout << "two" << endl; break;
            default: cout << "other" << endl; break;
        }
        return 0;
    }
    """
    out = t(src)
    assert 'switch' in out
    assert 'case 1:' in out
    assert 'printf' in out

# ── functions ─────────────────────────────────────────────────────────────────

def test_function():
    src = "int add(int a, int b) { return a + b; } int main() { return 0; }"
    out = t(src)
    assert 'int add(int a, int b)' in out

# ── enum ──────────────────────────────────────────────────────────────────────

def test_enum():
    src = "enum Color { RED, GREEN, BLUE }; int main() { return 0; }"
    out = t(src)
    assert 'enum Color' in out
    assert 'RED' in out

# ── const ─────────────────────────────────────────────────────────────────────

def test_const():
    src = "int main() { const int MAX = 100; return 0; }"
    out = t(src)
    assert 'const' in out
    assert '100' in out
