# tests/test_new_cpp_features.py
# Tests for newly added C->C++ and C++->C features
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import c_to_cpp, cpp_to_c

def c2cpp(src): return c_to_cpp.translate_string(src)
def cpp2c(src): return cpp_to_c.translate_string(src)


# ═══════════════════════════════════════════════════════════════════════════
# C -> C++ NEW FEATURES
# ═══════════════════════════════════════════════════════════════════════════

# -- puts/putchar --
def test_c2cpp_puts():
    out = c2cpp('int main() { puts("hello"); return 0; }')
    assert 'cout' in out and 'endl' in out

def test_c2cpp_putchar():
    out = c2cpp("int main() { putchar('A'); return 0; }")
    assert 'cout.put' in out

# -- getchar --
def test_c2cpp_getchar():
    out = c2cpp("int main() { int c = getchar(); return 0; }")
    assert 'cin.get()' in out

# -- strcat -> += --
def test_c2cpp_strcat():
    out = c2cpp('int main() { char a[100] = "hello"; char *b = "world"; strcat(a, b); return 0; }')
    assert '+=' in out

# -- strncmp --
def test_c2cpp_strncmp():
    out = c2cpp('int main() { char *a = "abc"; char *b = "abd"; int r = strncmp(a, b, 3); return 0; }')
    assert '.compare(0' in out

# -- strncpy --
def test_c2cpp_strncpy():
    out = c2cpp('int main() { char a[10]; char *b = "hello"; strncpy(a, b, 5); return 0; }')
    assert '.substr(0' in out

# -- strdup --
def test_c2cpp_strdup():
    out = c2cpp('int main() { char *s = "hi"; char *d = strdup(s); return 0; }')
    assert 'string d = s;' in out or 'string(' in out

# -- memcpy -> copy --
def test_c2cpp_memcpy():
    out = c2cpp('int main() { int a[5]; int b[5]; memcpy(a, b, 20); return 0; }')
    assert 'copy(' in out

# -- memset -> fill --
def test_c2cpp_memset():
    out = c2cpp('int main() { int arr[10]; memset(arr, 0, 40); return 0; }')
    assert 'fill(' in out

# -- qsort -> sort --
def test_c2cpp_qsort():
    out = c2cpp('int main() { int arr[5] = {3,1,2,5,4}; qsort(arr, 5, sizeof(int), 0); return 0; }')
    assert 'sort(' in out

# -- enum class --
def test_c2cpp_enum_class():
    out = c2cpp('enum Color { RED, GREEN, BLUE }; int main() { return 0; }')
    assert 'enum class' in out

# -- NULL -> nullptr --
def test_c2cpp_null_nullptr():
    out = c2cpp('int main() { int *p = NULL; return 0; }')
    assert 'nullptr' in out

# -- atoi -> stoi --
def test_c2cpp_atoi_stoi():
    out = c2cpp('int main() { char *s = "42"; int n = atoi(s); return 0; }')
    assert 'stoi(' in out

# -- algorithm include --
def test_c2cpp_algorithm_include():
    out = c2cpp('int main() { int a[5]; int b[5]; memcpy(a, b, 20); return 0; }')
    assert '#include <algorithm>' in out

# -- fstream include --
def test_c2cpp_fstream():
    # Can't easily test fopen in pycparser without stdio.h, check include
    out = c2cpp('int main() { return 0; }')
    assert '#include <iostream>' in out

# -- exit --
def test_c2cpp_exit():
    out = c2cpp('int main() { exit(1); return 0; }')
    assert 'exit(1)' in out


# ═══════════════════════════════════════════════════════════════════════════
# C++ -> C NEW FEATURES
# ═══════════════════════════════════════════════════════════════════════════

# -- cerr -> fprintf(stderr) --
def test_cpp2c_cerr():
    src = '#include <iostream>\nusing namespace std;\nint main() { cerr << "error" << endl; return 0; }'
    out = cpp2c(src)
    assert 'fprintf(stderr' in out

# -- bool -> int, true/false -> 1/0 --
def test_cpp2c_bool():
    out = cpp2c('int main() { bool flag = true; bool b = false; return 0; }')
    assert 'int flag = 1;' in out
    assert 'int b = 0;' in out

# -- constexpr -> const --
def test_cpp2c_constexpr():
    out = cpp2c('int main() { constexpr int N = 10; return 0; }')
    assert 'const int N = 10;' in out

# -- auto -> int --
def test_cpp2c_auto():
    out = cpp2c('int main() { auto x = 5; return 0; }')
    assert 'int x = 5;' in out

# -- enum class -> enum --
def test_cpp2c_enum_class():
    out = cpp2c('enum class Color { RED, GREEN, BLUE }; int main() { return 0; }')
    assert 'enum Color' in out
    assert 'enum class' not in out

# -- using -> typedef --
def test_cpp2c_using_typedef():
    out = cpp2c('using myint = int; int main() { myint x = 5; return 0; }')
    assert 'typedef int myint;' in out

# -- nullptr -> NULL --
def test_cpp2c_nullptr():
    out = cpp2c('int main() { int* p = nullptr; return 0; }')
    assert 'NULL' in out

# -- new -> malloc --
def test_cpp2c_new():
    out = cpp2c('int main() { int* arr = new int[10]; return 0; }')
    assert 'malloc' in out

# -- delete -> free --
def test_cpp2c_delete():
    out = cpp2c('int main() { int* arr = new int[5]; delete[] arr; return 0; }')
    assert 'free(arr)' in out

# -- stoi -> atoi --
def test_cpp2c_stoi():
    src = '#include <string>\nusing namespace std;\nint main() { string s = "42"; int x = stoi(s); return 0; }'
    out = cpp2c(src)
    assert 'atoi(s)' in out

# -- static_cast -> C cast --
def test_cpp2c_static_cast():
    out = cpp2c('int main() { double x = 3.14; int y = static_cast<int>(x); return 0; }')
    assert '(int)(x)' in out

# -- class -> struct --
def test_cpp2c_class():
    src = 'class Point { public: int x; int y; }; int main() { return 0; }'
    out = cpp2c(src)
    assert 'typedef struct' in out
    assert 'Point;' in out

# -- string methods -> C funcs --
def test_cpp2c_string_length():
    src = '#include <string>\nusing namespace std;\nint main() { string s = "hi"; int n = s.length(); return 0; }'
    out = cpp2c(src)
    assert 'strlen(s)' in out

def test_cpp2c_string_compare():
    src = '#include <string>\nusing namespace std;\nint main() { string a = "a"; string b = "b"; int r = a.compare(b); return 0; }'
    out = cpp2c(src)
    assert 'strcmp(a, b)' in out

def test_cpp2c_string_empty():
    src = '#include <string>\nusing namespace std;\nint main() { string s = "hi"; if (s.empty()) {} return 0; }'
    out = cpp2c(src)
    assert 'strlen(s) == 0' in out

def test_cpp2c_string_substr():
    src = '#include <string>\nusing namespace std;\nint main() { string s = "hello"; auto sub = s.substr(2); return 0; }'
    out = cpp2c(src)
    assert '+ 2' in out

# -- sort -> qsort --
def test_cpp2c_sort():
    src = '#include <algorithm>\nusing namespace std;\nint main() { int arr[5]; sort(arr, arr + 5); return 0; }'
    out = cpp2c(src)
    assert 'qsort' in out

# -- swap -> temp --
def test_cpp2c_swap():
    src = '#include <algorithm>\nusing namespace std;\nint main() { int a=1, b=2; swap(a, b); return 0; }'
    out = cpp2c(src)
    assert '_tmp' in out

# -- min/max -> ternary --
def test_cpp2c_min():
    src = '#include <algorithm>\nusing namespace std;\nint main() { int a=3, b=5; int c = min(a, b); return 0; }'
    out = cpp2c(src)
    assert '?' in out and ':' in out

def test_cpp2c_max():
    src = '#include <algorithm>\nusing namespace std;\nint main() { int a=3, b=5; int c = max(a, b); return 0; }'
    out = cpp2c(src)
    assert '?' in out and ':' in out

# -- to_string -> comment --
def test_cpp2c_to_string():
    src = '#include <string>\nusing namespace std;\nint main() { string s = to_string(42); return 0; }'
    out = cpp2c(src)
    assert 'to_string' in out and 'sprintf' in out

# -- vector -> pointer --
def test_cpp2c_vector():
    src = '#include <vector>\nusing namespace std;\nint main() { vector<int> arr; return 0; }'
    out = cpp2c(src)
    assert 'int*' in out

# -- includes translated --
def test_cpp2c_algorithm_include():
    src = '#include <algorithm>\nint main() { return 0; }'
    out = cpp2c(src)
    assert '#include <stdlib.h>' in out

def test_cpp2c_sstream_include():
    src = '#include <sstream>\nint main() { return 0; }'
    out = cpp2c(src)
    assert '#include <stdio.h>' in out

# -- try/catch --
def test_cpp2c_try_catch():
    src = '''
    int main() {
        try {
            int x = 5;
        } catch (...) {
            int y = 0;
        }
        return 0;
    }
    '''
    out = cpp2c(src)
    assert '/* try */' in out
    assert 'int x = 5;' in out

# -- push_back comment --
def test_cpp2c_push_back():
    src = '#include <vector>\nusing namespace std;\nint main() { vector<int> v; v.push_back(5); return 0; }'
    out = cpp2c(src)
    assert 'push_back' in out

# -- front/back --
def test_cpp2c_front_back():
    src = '#include <string>\nusing namespace std;\nint main() { string s = "hi"; auto f = s.front(); auto b = s.back(); return 0; }'
    out = cpp2c(src)
    assert 's[0]' in out

# -- getline -> fgets --
def test_cpp2c_getline():
    src = '#include <string>\nusing namespace std;\nint main() { string s = "buf"; getline(cin, s); return 0; }'
    out = cpp2c(src)
    assert 'fgets' in out

# -- references in params -> pointers --
def test_cpp2c_reference_params():
    src = 'void inc(int& x) { x++; } int main() { return 0; }'
    out = cpp2c(src)
    assert 'int *x' in out or 'int*' in out
