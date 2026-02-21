#!/usr/bin/env python3
"""Run all samples through translators + compiler verification."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import java_to_c, c_to_java
from verify import compile_c_wsl, compile_java_wsl

SAMPLES = os.path.join(os.path.dirname(__file__), 'samples')

results = []

# Java -> C samples
for fname in sorted(os.listdir(SAMPLES)):
    path = os.path.join(SAMPLES, fname)
    if fname.endswith('.java'):
        print(f'\n{"="*50}')
        print(f'  Java->C: {fname}')
        print(f'{"="*50}')
        try:
            c_code = java_to_c.translate_file(path)
            print(f'  [OK] Translated ({len(c_code)} chars)')
            ok, msg = compile_c_wsl(c_code)
            status = 'PASS' if ok else 'FAIL'
            print(f'  gcc [{status}]: {msg[:150]}')
            results.append((fname, 'java->c', status, msg[:100]))
        except Exception as e:
            print(f'  [ERROR] {e}')
            results.append((fname, 'java->c', 'ERROR', str(e)[:100]))

    elif fname.endswith('.c'):
        print(f'\n{"="*50}')
        print(f'  C->Java: {fname}')
        print(f'{"="*50}')
        try:
            java_code = c_to_java.translate_file(path)
            print(f'  [OK] Translated ({len(java_code)} chars)')
            ok, msg = compile_java_wsl(java_code)
            status = 'PASS' if ok else 'FAIL'
            print(f'  javac [{status}]: {msg[:150]}')
            results.append((fname, 'c->java', status, msg[:100]))
        except Exception as e:
            print(f'  [ERROR] {e}')
            results.append((fname, 'c->java', 'ERROR', str(e)[:100]))

# Summary
print(f'\n\n{"="*50}')
print(f'  SUMMARY')
print(f'{"="*50}')
for fname, direction, status, msg in results:
    icon = 'v' if status == 'PASS' else 'X'
    print(f'  [{icon}] {fname:30s} {direction:10s} {status}')

passed = sum(1 for _,_,s,_ in results if s=='PASS')
total  = len(results)
print(f'\n  {passed}/{total} PASSED')
sys.exit(0 if passed == total else 1)
