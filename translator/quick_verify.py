"""Quick verification of each sample."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import java_to_c, c_to_java
from verify import compile_c_wsl, compile_java_wsl

SAMPLES = os.path.join(os.path.dirname(__file__), 'samples')

tests = [
    ('all_features.java', 'j2c'),
    ('all_features.c',    'c2j'),
    ('calculator.c',      'c2j'),
    ('fibonacci.java',    'j2c'),
    ('hashmap_strings.java', 'j2c'),
]

for f, d in tests:
    path = os.path.join(SAMPLES, f)
    try:
        if d == 'j2c':
            code = java_to_c.translate_file(path)
            ok, msg = compile_c_wsl(code)
            compiler = 'gcc'
        else:
            code = c_to_java.translate_file(path)
            ok, msg = compile_java_wsl(code)
            compiler = 'javac'
        status = 'PASS' if ok else 'FAIL'
        print(f"  [{status}] {f:30s} {compiler:6s} {msg[:120]}")
        if not ok:
            print(f"        DETAILS: {msg}")
    except Exception as e:
        print(f"  [ERR ] {f:30s} {e}")

