# debug_bugs.py
import sys, os, tempfile
from traceback import print_exc
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import c_to_java, java_to_c, c_to_cpp, cpp_to_c
from verify import compile_c_wsl, compile_java_wsl, compile_cpp_wsl

C_POINTERS = '#include <stdio.h>\n#include <stdlib.h>\nint main() { int *p = (int*)malloc(sizeof(int)); *p = 42; printf("%d\\n", *p); free(p); return 0; }'
C_STRUCT = '#include <stdio.h>\nstruct Point { int x; int y; };\nint main() { struct Point p; p.x = 10; p.y = 20; printf("(%d,%d)\\n", p.x, p.y); return 0; }'

print("=== C -> Java Pointers ===")
with tempfile.NamedTemporaryFile(suffix='.c', mode='w', encoding='utf-8', delete=False) as f:
    f.write(C_POINTERS); tmp = f.name
java_ptr = c_to_java.translate_file(tmp)
os.unlink(tmp)
print(java_ptr)
ok, msg = compile_java_wsl(java_ptr)
print(f"Compile: {ok}, {msg[:100]}")

print("\n=== C -> Java Struct ===")
with tempfile.NamedTemporaryFile(suffix='.c', mode='w', encoding='utf-8', delete=False) as f:
    f.write(C_STRUCT); tmp = f.name
java_struct = c_to_java.translate_file(tmp)
os.unlink(tmp)
print(java_struct)
ok, msg = compile_java_wsl(java_struct)
print(f"Compile: {ok}, {msg[:100]}")

JAVA_ARRAYS = 'public class Main { public static void main(String[] args) { int[] arr = {5,3,1,4,2}; for(int i=0;i<arr.length;i++) System.out.print(arr[i]+" "); } }'
print("\n=== Java -> C Arrays ===")
c_arr = java_to_c.translate_string(JAVA_ARRAYS)
print(c_arr)
ok, msg = compile_c_wsl(c_arr)
print(f"Compile: {ok}, {msg[:100]}")

JAVA_MATH = 'public class Main { public static void main(String[] args) { double x = 3.14; System.out.printf("sqrt=%.2f\\n", Math.sqrt(x)); System.out.printf("abs=%d\\n", Math.abs(-5)); } }'
print("\n=== Java -> C Math ===")
c_math = java_to_c.translate_string(JAVA_MATH)
print(c_math)
ok, msg = compile_c_wsl(c_math)
print(f"Compile: {ok}, {msg[:100]}")

CPP_ENUM = '#include <iostream>\nusing namespace std;\nenum class Color { RED, GREEN, BLUE };\nint main() { Color c = Color::RED; return 0; }'
print("\n=== C++ -> C Enum ===")
c_enum = cpp_to_c.translate_string(CPP_ENUM)
print(c_enum)
ok, msg = compile_c_wsl(c_enum)
print(f"Compile: {ok}, {msg[:100]}")
