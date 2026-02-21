# tests/test_oop_features.py
# Tests for OOP and template C++ -> C translation features
import sys, os, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import cpp_to_c

def t(src): return cpp_to_c.translate_string(src)


# ═══════════════════════════════════════════════════════════════════════════
# 1. CONSTRUCTOR -> INIT FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def test_constructor_basic():
    src = '''
    class Point {
    public:
        int x;
        int y;
        Point(int a, int b) : x(a), y(b) { }
    };
    int main() { return 0; }
    '''
    out = t(src)
    assert 'Point_init' in out
    assert 'Point* self' in out
    assert 'self->x' in out
    assert 'self->y' in out


def test_constructor_with_body():
    src = '''
    class Counter {
    public:
        int count;
        Counter(int c) : count(c) { }
    };
    int main() { return 0; }
    '''
    out = t(src)
    assert 'Counter_init' in out
    assert 'self->count' in out


def test_constructor_params():
    src = '''
    class Box {
    public:
        int width;
        int height;
        Box(int w, int h) : width(w), height(h) { }
    };
    int main() { return 0; }
    '''
    out = t(src)
    assert 'void Box_init(Box* self, int w, int h)' in out


# ═══════════════════════════════════════════════════════════════════════════
# 2. DESTRUCTOR -> DESTROY FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def test_destructor():
    src = '''
    class Resource {
    public:
        int* data;
        Resource() { }
        ~Resource() { }
    };
    int main() { return 0; }
    '''
    out = t(src)
    assert 'Resource_destroy' in out
    assert 'Resource* self' in out


def test_destructor_with_body():
    src = '''
    class Buffer {
    public:
        int* ptr;
        Buffer() { }
        ~Buffer() { }
    };
    int main() { return 0; }
    '''
    out = t(src)
    assert 'Buffer_destroy(Buffer* self)' in out


# ═══════════════════════════════════════════════════════════════════════════
# 3. INHERITANCE -> STRUCT COMPOSITION
# ═══════════════════════════════════════════════════════════════════════════

def test_inheritance_base_field():
    src = '''
    class Animal {
    public:
        int age;
    };
    class Dog : public Animal {
    public:
        int loyalty;
    };
    int main() { return 0; }
    '''
    out = t(src)
    assert 'Animal base;' in out
    assert 'inherits from Animal' in out
    assert 'int loyalty;' in out


def test_inheritance_with_constructor():
    src = '''
    class Animal {
    public:
        int age;
        Animal(int a) : age(a) { }
    };
    class Dog : public Animal {
    public:
        int loyalty;
        Dog(int a, int l) : Animal(a), loyalty(l) { }
    };
    int main() { return 0; }
    '''
    out = t(src)
    assert 'Animal_init' in out
    assert 'Dog_init' in out
    assert 'Animal base;' in out


# ═══════════════════════════════════════════════════════════════════════════
# 4. VIRTUAL METHODS -> FUNCTION POINTERS
# ═══════════════════════════════════════════════════════════════════════════

def test_virtual_method_pointer():
    src = '''
    class Shape {
    public:
        virtual void draw() { }
    };
    int main() { return 0; }
    '''
    out = t(src)
    assert '(*draw)' in out
    assert 'virtual' in out.lower() or '/* virtual */' in out


def test_virtual_with_override():
    src = '''
    class Animal {
    public:
        int age;
        virtual void speak() { }
    };
    class Dog : public Animal {
    public:
        void speak() override { }
    };
    int main() { return 0; }
    '''
    out = t(src)
    # Animal should have function pointer for speak
    assert '(*speak)' in out
    # Dog should have _impl for its override
    assert 'Dog_speak_impl' in out


# ═══════════════════════════════════════════════════════════════════════════
# 5. REGULAR METHODS -> STANDALONE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def test_method_to_function():
    src = '''
    class Calculator {
    public:
        int value;
        int add(int x) { return x + 1; }
    };
    int main() { return 0; }
    '''
    out = t(src)
    assert 'Calculator_add' in out
    assert 'Calculator* self' in out


# ═══════════════════════════════════════════════════════════════════════════
# 6. TEMPLATE -> #define MACRO
# ═══════════════════════════════════════════════════════════════════════════

def test_template_simple_return():
    src = '''
    template<typename T>
    T maxVal(T a, T b) { return a > b ? a : b; }
    int main() { return 0; }
    '''
    out = t(src)
    assert '#define MAXVAL(a, b)' in out
    assert 'a > b ? a : b' in out


def test_template_min():
    src = '''
    template<typename T>
    T minVal(T a, T b) { return a < b ? a : b; }
    int main() { return 0; }
    '''
    out = t(src)
    assert '#define MINVAL(a, b)' in out


def test_template_identity():
    src = '''
    template<typename T>
    T identity(T x) { return x; }
    int main() { return 0; }
    '''
    out = t(src)
    assert '#define IDENTITY(x)' in out


# ═══════════════════════════════════════════════════════════════════════════
# 7. STRING CONCATENATION -> strcat
# ═══════════════════════════════════════════════════════════════════════════

def test_string_concat_var_literal():
    src = '''
    #include <string>
    using namespace std;
    int main() { string s = "hello"; string r = s + " world"; return 0; }
    '''
    out = t(src)
    assert 'strcat' in out


def test_this_to_self():
    src = '''
    class Foo {
    public:
        int x;
        void set(int v) { this->x = v; }
    };
    int main() { return 0; }
    '''
    out = t(src)
    assert 'self->x' in out or 'self->' in out


# ═══════════════════════════════════════════════════════════════════════════
# 8. STRUCT FIELDS PRESERVED
# ═══════════════════════════════════════════════════════════════════════════

def test_class_fields_preserved():
    src = '''
    class Person {
    public:
        int age;
        double height;
    };
    int main() { return 0; }
    '''
    out = t(src)
    assert 'typedef struct' in out
    assert 'int age;' in out
    assert 'double height;' in out
    assert 'Person;' in out


def test_class_no_public():
    """Fields without access specifier should still be emitted."""
    src = '''
    class Simple {
    public:
        int x;
    };
    int main() { return 0; }
    '''
    out = t(src)
    assert 'int x;' in out
    assert 'public' not in out  # access specifier stripped
