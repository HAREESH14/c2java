"""
Accuracy metrics: Run 20 diverse test programs through all 4 translation 
directions and report compile success rate.
"""
import sys, os, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import c_to_java, java_to_c, c_to_cpp, cpp_to_c
from verify import compile_c_wsl, compile_java_wsl, compile_cpp_wsl

# ─── 10 C programs ─────────────────────────────────────────────────────────
C_PROGRAMS = {
    "hello_world": '#include <stdio.h>\nint main() { printf("Hello World\\n"); return 0; }',
    
    "factorial": '#include <stdio.h>\nint fact(int n) { if (n<=1) return 1; return n*fact(n-1); }\nint main() { printf("%d\\n", fact(5)); return 0; }',
    
    "fibonacci": '#include <stdio.h>\nint fib(int n) { if (n<=1) return n; return fib(n-1)+fib(n-2); }\nint main() { int i; for(i=0;i<10;i++) printf("%d ",fib(i)); return 0; }',
    
    "arrays": '#include <stdio.h>\nint main() { int arr[5] = {5,3,1,4,2}; int i,t; for(i=0;i<4;i++) { if(arr[i]>arr[i+1]) { t=arr[i]; arr[i]=arr[i+1]; arr[i+1]=t; } } for(i=0;i<5;i++) printf("%d ",arr[i]); return 0; }',
    
    "strings": '#include <stdio.h>\n#include <string.h>\nint main() { char s[100] = "hello"; int len = strlen(s); printf("len=%d\\n", len); return 0; }',
    
    "pointers": '#include <stdio.h>\n#include <stdlib.h>\nint main() { int *p = (int*)malloc(sizeof(int)); *p = 42; printf("%d\\n", *p); free(p); return 0; }',
    
    "struct": '#include <stdio.h>\nstruct Point { int x; int y; };\nint main() { struct Point p; p.x = 10; p.y = 20; printf("(%d,%d)\\n", p.x, p.y); return 0; }',
    
    "switch_case": '#include <stdio.h>\nint main() { int day = 3; switch(day) { case 1: printf("Mon\\n"); break; case 2: printf("Tue\\n"); break; default: printf("Other\\n"); } return 0; }',
    
    "while_loop": '#include <stdio.h>\nint main() { int i = 0, sum = 0; while(i < 10) { sum += i; i++; } printf("sum=%d\\n", sum); return 0; }',
    
    "math_ops": '#include <stdio.h>\n#include <math.h>\nint main() { double x = 3.14; printf("sin=%.2f cos=%.2f\\n", sin(x), cos(x)); return 0; }',
}

# ─── 10 Java programs ──────────────────────────────────────────────────────
JAVA_PROGRAMS = {
    "hello_java": 'public class Main { public static void main(String[] args) { System.out.println("Hello Java"); } }',
    
    "factorial_java": 'public class Main { static int fact(int n) { if (n<=1) return 1; return n*fact(n-1); } public static void main(String[] args) { System.out.println(fact(5)); } }',
    
    "fibonacci_java": 'public class Main { static int fib(int n) { if (n<=1) return n; return fib(n-1)+fib(n-2); } public static void main(String[] args) { for(int i=0;i<10;i++) System.out.print(fib(i)+" "); } }',
    
    "arrays_java": 'public class Main { public static void main(String[] args) { int[] arr = {5,3,1,4,2}; for(int i=0;i<arr.length;i++) System.out.print(arr[i]+" "); } }',
    
    "strings_java": 'public class Main { public static void main(String[] args) { String s = "hello"; System.out.println("len="+s.length()); System.out.println(s.toUpperCase()); } }',

    "if_else_java": 'public class Main { public static void main(String[] args) { int x = 10; if (x > 5) { System.out.println("big"); } else { System.out.println("small"); } } }',
    
    "while_java": 'public class Main { public static void main(String[] args) { int i=0, sum=0; while(i<10) { sum+=i; i++; } System.out.println("sum="+sum); } }',
    
    "switch_java": 'public class Main { public static void main(String[] args) { int day=2; switch(day) { case 1: System.out.println("Mon"); break; case 2: System.out.println("Tue"); break; default: System.out.println("Other"); } } }',
    
    "for_loop_java": 'public class Main { public static void main(String[] args) { for(int i=1; i<=5; i++) { System.out.printf("i=%d\\n", i); } } }',
    
    "math_java": 'public class Main { public static void main(String[] args) { double x = 3.14; System.out.printf("sqrt=%.2f\\n", Math.sqrt(x)); System.out.printf("abs=%d\\n", Math.abs(-5)); } }',
}

# ─── 10 C++ programs ───────────────────────────────────────────────────────
CPP_PROGRAMS = {
    "hello_cpp": '#include <iostream>\nusing namespace std;\nint main() { cout << "Hello C++" << endl; return 0; }',
    
    "class_basic": '#include <iostream>\nusing namespace std;\nclass Point { public: int x; int y; };\nint main() { Point p; p.x = 10; p.y = 20; cout << p.x << "," << p.y << endl; return 0; }',
    
    "string_ops": '#include <iostream>\n#include <string>\nusing namespace std;\nint main() { string s = "hello"; cout << s.length() << endl; return 0; }',
    
    "new_delete": '#include <iostream>\nusing namespace std;\nint main() { int* p = new int(42); cout << *p << endl; delete p; return 0; }',
    
    "bool_cpp": '#include <iostream>\nusing namespace std;\nint main() { bool flag = true; if (flag) cout << "yes" << endl; return 0; }',
    
    "auto_cpp": '#include <iostream>\nusing namespace std;\nint main() { auto x = 42; cout << x << endl; return 0; }',
    
    "nullptr_cpp": '#include <iostream>\nusing namespace std;\nint main() { int* p = nullptr; if (p == nullptr) cout << "null" << endl; return 0; }',
    
    "static_cast_cpp": '#include <iostream>\nusing namespace std;\nint main() { double d = 3.14; int i = static_cast<int>(d); cout << i << endl; return 0; }',
    
    "for_loop_cpp": '#include <iostream>\nusing namespace std;\nint main() { for(int i=0; i<5; i++) { cout << i << " "; } cout << endl; return 0; }',
    
    "enum_cpp": '#include <iostream>\nusing namespace std;\nenum class Color { RED, GREEN, BLUE };\nint main() { Color c = Color::RED; return 0; }',
}


def run_metrics():
    results = []

    # C -> Java
    print("=" * 60)
    print("  C -> Java (10 programs)")
    print("=" * 60)
    for name, src in C_PROGRAMS.items():
        try:
            # Write to temp file for pycparser
            with tempfile.NamedTemporaryFile(suffix='.c', mode='w', 
                                             encoding='utf-8', delete=False) as f:
                f.write(src); tmp = f.name
            java_out = c_to_java.translate_file(tmp)
            os.unlink(tmp)
            ok, msg = compile_java_wsl(java_out)
            status = "PASS" if ok else "FAIL"
        except Exception as e:
            status = "ERROR"
            msg = str(e)[:50]
        results.append(("C->Java", name, status))
        print(f"  {status:5s}  {name}")

    # C -> C++
    print("\n" + "=" * 60)
    print("  C -> C++ (10 programs)")
    print("=" * 60)
    for name, src in C_PROGRAMS.items():
        try:
            with tempfile.NamedTemporaryFile(suffix='.c', mode='w',
                                             encoding='utf-8', delete=False) as f:
                f.write(src); tmp = f.name
            cpp_out = c_to_cpp.translate_file(tmp)
            os.unlink(tmp)
            ok, msg = compile_cpp_wsl(cpp_out)
            status = "PASS" if ok else "FAIL"
        except Exception as e:
            status = "ERROR"
            msg = str(e)[:50]
        results.append(("C->C++", name, status))
        print(f"  {status:5s}  {name}")

    # Java -> C
    print("\n" + "=" * 60)
    print("  Java -> C (10 programs)")
    print("=" * 60)
    for name, src in JAVA_PROGRAMS.items():
        try:
            c_out = java_to_c.translate_string(src)
            ok, msg = compile_c_wsl(c_out)
            status = "PASS" if ok else "FAIL"
        except Exception as e:
            status = "ERROR"
            msg = str(e)[:50]
        results.append(("Java->C", name, status))
        print(f"  {status:5s}  {name}")

    # C++ -> C
    print("\n" + "=" * 60)
    print("  C++ -> C (10 programs)")
    print("=" * 60)
    for name, src in CPP_PROGRAMS.items():
        try:
            c_out = cpp_to_c.translate_string(src)
            ok, msg = compile_c_wsl(c_out)
            status = "PASS" if ok else "FAIL"
        except Exception as e:
            status = "ERROR"
            msg = str(e)[:50]
        results.append(("C++->C", name, status))
        print(f"  {status:5s}  {name}")

    # Summary
    print("\n" + "=" * 60)
    print("  ACCURACY SUMMARY")
    print("=" * 60)
    for direction in ["C->Java", "C->C++", "Java->C", "C++->C"]:
        dir_results = [r for r in results if r[0] == direction]
        passed = sum(1 for r in dir_results if r[2] == "PASS")
        total = len(dir_results)
        pct = (passed / total * 100) if total > 0 else 0
        print(f"  {direction:10s}: {passed}/{total} ({pct:.0f}%)")

    total_pass = sum(1 for r in results if r[2] == "PASS")
    total = len(results)
    pct = (total_pass / total * 100) if total > 0 else 0
    print(f"  {'OVERALL':10s}: {total_pass}/{total} ({pct:.0f}%)")


if __name__ == '__main__':
    run_metrics()
