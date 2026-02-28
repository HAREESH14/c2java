#!/usr/bin/env python3
"""
Batch test: translate all .c files from samples/ using the Clang translator,
then compile with javac to verify.
"""
import os, sys, tempfile, subprocess, glob

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'samples')
SCRIPT = os.path.join(os.path.dirname(__file__), 'c_to_java_clang.py')

def compile_java(java_src: str) -> tuple:
    """Write java source to tmp file and compile with javac."""
    tmpdir = tempfile.mkdtemp(prefix='j2c_')
    fpath = os.path.join(tmpdir, 'Main.java')
    with open(fpath, 'w') as f:
        f.write(java_src)
    result = subprocess.run(['javac', fpath], capture_output=True, text=True, timeout=10)
    # cleanup
    for f in glob.glob(os.path.join(tmpdir, '*')):
        os.unlink(f)
    os.rmdir(tmpdir)
    if result.returncode == 0:
        return True, 'OK'
    return False, result.stderr[:200]


def main():
    import c_to_java_clang as clang_tr

    c_files = sorted(glob.glob(os.path.join(SAMPLES_DIR, '*.c')))
    total = len(c_files)
    passed = 0
    failed = 0
    errors = []

    print(f"Testing {total} C files through Clang translator...\n")
    print(f"{'File':<40} {'Status'}")
    print('-' * 60)

    for cfile in c_files:
        name = os.path.basename(cfile)
        try:
            java_out = clang_tr.translate_file(cfile)
            ok, msg = compile_java(java_out)
            if ok:
                print(f"  v {name:<38} PASS")
                passed += 1
            else:
                print(f"  x {name:<38} FAIL")
                errors.append((name, msg))
                failed += 1
        except Exception as e:
            print(f"  ! {name:<38} ERROR: {str(e)[:50]}")
            errors.append((name, str(e)[:100]))
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"  TOTAL: {total} | PASS: {passed} | FAIL: {failed}")
    print(f"  Accuracy: {passed/total*100:.0f}%")
    if errors:
        print(f"\n  ERRORS:")
        for name, msg in errors:
            print(f"    {name}: {msg[:80]}")


if __name__ == '__main__':
    main()
