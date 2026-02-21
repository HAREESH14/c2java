#!/usr/bin/env python3
# =============================================================================
#  main.py  --  Unified Multi-Language Translator
#
#  Supports 4 translation directions + multi-file/folder batch mode:
#
#  Single file:
#    uv run python src/main.py input.java          -> Java -> C
#    uv run python src/main.py input.c             -> C   -> Java
#    uv run python src/main.py input.c   --to cpp  -> C   -> C++
#    uv run python src/main.py input.cpp           -> C++ -> C
#
#  Folder batch mode:
#    uv run python src/main.py samples/            -> translate all files
#    uv run python src/main.py samples/ --to cpp   -> all C files -> C++
#    uv run python src/main.py samples/ --output out/  -> save to out/
#    uv run python src/main.py samples/ --verify   -> translate + compile
#
#  Flags:
#    --verify    compile output with gcc/g++/javac
#    --ast       show AST before translation
#    --to cpp    force C -> C++ direction
#    --output DIR  output directory (batch mode)
#    --demo      run built-in demos
# =============================================================================

import sys, os, pathlib, tempfile, time
sys.path.insert(0, os.path.dirname(__file__))

import java_to_c
import c_to_java
import c_to_cpp
import cpp_to_c
from verify import compile_c_wsl, compile_java_wsl, compile_cpp_wsl


BANNER = """\
+================================================+
|    Multi-Language Source-to-Source Transpiler    |
|                                                |
|    Java <-> C <-> C++                          |
|                                                |
|    Java parser : javalang                      |
|    C    parser : pycparser                     |
|    C++  parser : tree-sitter (AST)             |
|                                                |
|    Modes: single file, folder batch            |
+================================================+
"""

JAVA_DEMO = """\
import java.util.HashMap;

public class Main {

    public static int add(int a, int b) { return a + b; }

    public static void main(String[] args) {
        int x = 10, y = 20;
        int result = add(x, y);
        System.out.printf("Sum: %d%n", result);

        for (int i = 0; i < 5; i++) {
            if (i == 2) continue;
            System.out.println(i);
        }

        int[] primes = {2, 3, 5, 7, 11};
        for (int p : primes) System.out.println(p);

        int day = 2;
        switch (day) {
            case 1: System.out.println("Mon"); break;
            case 2: System.out.println("Tue"); break;
            default: System.out.println("Other"); break;
        }

        HashMap<Integer,Integer> map = new HashMap<>();
        map.put(1, 100);
        if (map.containsKey(1)) System.out.printf("Val: %d%n", map.get(1));
    }
}
"""

C_DEMO = """\
#include <stdio.h>

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int main() {
    int i;
    for (i = 1; i <= 5; i++) {
        printf("fact(%d) = %d\\n", i, factorial(i));
    }
    int x;
    scanf("%d", &x);
    printf("You entered: %d\\n", x);
    return 0;
}
"""


# ---------------------------------------------------------------------------
#  Single-file translation functions
# ---------------------------------------------------------------------------

def run_java_to_c(source: str, out_name: str,
                  show_ast: bool, verify: bool, quiet: bool = False):
    if not quiet:
        print(f'\n  Mode     : Java -> C')
        print(f'  Parser   : javalang (Java AST)')
        print(f'  Backend  : pycparser (C code gen)')
        print('-' * 48)

    if show_ast:
        try:
            import javalang
            tree = javalang.parse.parse(source)
            print('\n[javalang AST]')
            print(tree)
            print()
        except Exception as e:
            print(f'[AST] {e}')

    try:
        c_code = java_to_c.translate_string(source)
    except (ValueError, Exception) as e:
        if quiet:
            return None, str(e)
        print(f'[ERROR] {e}')
        sys.exit(1)

    if not quiet:
        print('\n[Generated C Code]')
        print(c_code)

    with open(out_name, 'w', encoding='utf-8') as f:
        f.write(c_code)
    if not quiet:
        print(f'\n[OK] Saved -> {out_name}')

    if verify:
        if not quiet:
            print('\n[WSL gcc] Compiling generated C...')
        ok, msg = compile_c_wsl(c_code)
        if not quiet:
            status  = 'PASS' if ok else 'FAIL'
            print(f'  gcc [{status}]: {msg}')
        return c_code, ('PASS' if ok else f'FAIL: {msg}')

    return c_code, 'OK'


def run_c_to_java(path: str, out_name: str, show_ast: bool,
                  verify: bool = False, quiet: bool = False):
    if not quiet:
        print(f'\n  Mode     : C -> Java')
        print(f'  Parser   : pycparser (C AST)')
        print(f'  Backend  : string emitter (Java)')
        print('-' * 48)

    if show_ast:
        try:
            import pycparser, re
            src = open(path, encoding='utf-8').read()
            src = re.sub(r'//.*?$|/\*.*?\*/', '', src, flags=re.M|re.S)
            src = '\n'.join(l for l in src.splitlines()
                            if not l.strip().startswith('#'))
            parser = pycparser.CParser()
            ast    = parser.parse(src)
            print('\n[pycparser AST]')
            ast.show(attrnames=True, nodenames=True)
            print()
        except Exception as e:
            print(f'[AST] {e}')

    try:
        java_code = c_to_java.translate_file(path)
    except (ValueError, Exception) as e:
        if quiet:
            return None, str(e)
        print(f'[ERROR] {e}')
        sys.exit(1)

    if not quiet:
        print('\n[Generated Java Code]')
        print(java_code)

    with open(out_name, 'w', encoding='utf-8') as f:
        f.write(java_code)
    if not quiet:
        print(f'\n[OK] Saved -> {out_name}')

    if verify:
        if not quiet:
            print('\n[WSL javac] Compiling generated Java...')
        ok, msg = compile_java_wsl(java_code)
        if not quiet:
            status  = 'PASS' if ok else 'FAIL'
            print(f'  javac [{status}]: {msg}')
        return java_code, ('PASS' if ok else f'FAIL: {msg}')

    return java_code, 'OK'


def run_c_to_cpp(path: str, out_name: str, show_ast: bool,
                 verify: bool = False, quiet: bool = False):
    if not quiet:
        print(f'\n  Mode     : C -> C++')
        print(f'  Parser   : pycparser (C AST)')
        print(f'  Backend  : string emitter (C++)')
        print('-' * 48)

    if show_ast:
        try:
            import pycparser, re
            src = open(path, encoding='utf-8').read()
            src = re.sub(r'//.*?$|/\*.*?\*/', '', src, flags=re.M|re.S)
            src = '\n'.join(l for l in src.splitlines()
                            if not l.strip().startswith('#'))
            parser = pycparser.CParser()
            ast    = parser.parse(src)
            print('\n[pycparser AST]')
            ast.show(attrnames=True, nodenames=True)
            print()
        except Exception as e:
            print(f'[AST] {e}')

    try:
        cpp_code = c_to_cpp.translate_file(path)
    except (ValueError, Exception) as e:
        if quiet:
            return None, str(e)
        print(f'[ERROR] {e}')
        sys.exit(1)

    if not quiet:
        print('\n[Generated C++ Code]')
        print(cpp_code)

    with open(out_name, 'w', encoding='utf-8') as f:
        f.write(cpp_code)
    if not quiet:
        print(f'\n[OK] Saved -> {out_name}')

    if verify:
        if not quiet:
            print('\n[WSL g++] Compiling generated C++...')
        ok, msg = compile_cpp_wsl(cpp_code)
        if not quiet:
            status  = 'PASS' if ok else 'FAIL'
            print(f'  g++ [{status}]: {msg}')
        return cpp_code, ('PASS' if ok else f'FAIL: {msg}')

    return cpp_code, 'OK'


def run_cpp_to_c(source: str, out_name: str,
                 show_ast: bool, verify: bool = False, quiet: bool = False):
    if not quiet:
        print(f'\n  Mode     : C++ -> C')
        print(f'  Parser   : tree-sitter (C++ AST)')
        print(f'  Backend  : string emitter (C)')
        print('-' * 48)

    try:
        c_code = cpp_to_c.translate_string(source)
    except (ValueError, Exception) as e:
        if quiet:
            return None, str(e)
        print(f'[ERROR] {e}')
        sys.exit(1)

    if not quiet:
        print('\n[Generated C Code]')
        print(c_code)

    with open(out_name, 'w', encoding='utf-8') as f:
        f.write(c_code)
    if not quiet:
        print(f'\n[OK] Saved -> {out_name}')

    if verify:
        if not quiet:
            print('\n[WSL gcc] Compiling generated C...')
        ok, msg = compile_c_wsl(c_code)
        if not quiet:
            status  = 'PASS' if ok else 'FAIL'
            print(f'  gcc [{status}]: {msg}')
        return c_code, ('PASS' if ok else f'FAIL: {msg}')

    return c_code, 'OK'


# ---------------------------------------------------------------------------
#  Multi-file / folder batch mode
# ---------------------------------------------------------------------------

# File extensions we scan for
SOURCE_EXTS = {'.c', '.java', '.cpp', '.h', '.hpp'}

def discover_files(folder: str) -> list:
    """Recursively discover source files in a folder."""
    files = []
    folder = os.path.abspath(folder)
    for root, dirs, filenames in os.walk(folder):
        # Skip hidden dirs and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for name in sorted(filenames):
            ext = pathlib.Path(name).suffix.lower()
            if ext in SOURCE_EXTS:
                files.append(os.path.join(root, name))
    return files


def get_translation_direction(ext: str, to_cpp: bool):
    """Determine translation direction from file extension."""
    if ext == '.java':
        return 'java_to_c'
    elif ext == '.c':
        return 'c_to_cpp' if to_cpp else 'c_to_java'
    elif ext == '.cpp':
        return 'cpp_to_c'
    elif ext in ('.h', '.hpp'):
        return 'header'  # headers are copied/skipped
    return None


def get_output_ext(direction: str) -> str:
    """Get the output file extension for a translation direction."""
    return {
        'java_to_c': '.c',
        'c_to_java': '.java',
        'c_to_cpp':  '.cpp',
        'cpp_to_c':  '.c',
    }.get(direction, '')


def run_batch(folder: str, output_dir: str, to_cpp: bool,
              verify: bool, show_ast: bool):
    """Translate all source files in a folder."""
    folder = os.path.abspath(folder)
    files = discover_files(folder)

    if not files:
        print(f'[WARNING] No source files found in: {folder}')
        return

    # Create output directory
    if output_dir:
        output_dir = os.path.abspath(output_dir)
    else:
        output_dir = os.path.join(folder, 'translated')
    os.makedirs(output_dir, exist_ok=True)

    print(f'\n  Batch Mode')
    print(f'  Input     : {folder}')
    print(f'  Output    : {output_dir}')
    print(f'  Files     : {len(files)}')
    if to_cpp:
        print(f'  C target  : C++ (--to cpp)')
    print(f'  Verify    : {"yes" if verify else "no"}')
    print('=' * 60)

    results = []
    start_time = time.time()

    for filepath in files:
        rel_path = os.path.relpath(filepath, folder)
        ext = pathlib.Path(filepath).suffix.lower()
        stem = pathlib.Path(filepath).stem
        direction = get_translation_direction(ext, to_cpp)

        if direction is None:
            results.append((rel_path, 'SKIP', 'Unknown file type'))
            continue

        if direction == 'header':
            # Copy header files to output as-is
            out_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(content)
            results.append((rel_path, 'COPY', 'Header file copied'))
            continue

        out_ext = get_output_ext(direction)
        # Preserve subdirectory structure
        rel_dir = os.path.dirname(rel_path)
        out_subdir = os.path.join(output_dir, rel_dir) if rel_dir else output_dir
        os.makedirs(out_subdir, exist_ok=True)
        out_path = os.path.join(out_subdir, stem + out_ext)

        arrow = {'java_to_c': 'Java->C', 'c_to_java': 'C->Java',
                 'c_to_cpp': 'C->C++', 'cpp_to_c': 'C++->C'}[direction]
        print(f'\n  [{arrow}] {rel_path} -> {os.path.relpath(out_path, output_dir)}')

        try:
            if direction == 'java_to_c':
                with open(filepath, 'r', encoding='utf-8') as f:
                    source = f.read()
                _, status = run_java_to_c(source, out_path, show_ast, verify, quiet=True)

            elif direction == 'c_to_java':
                _, status = run_c_to_java(filepath, out_path, show_ast, verify, quiet=True)

            elif direction == 'c_to_cpp':
                _, status = run_c_to_cpp(filepath, out_path, show_ast, verify, quiet=True)

            elif direction == 'cpp_to_c':
                with open(filepath, 'r', encoding='utf-8') as f:
                    source = f.read()
                _, status = run_cpp_to_c(source, out_path, show_ast, verify, quiet=True)

            if status is None:
                status = 'ERROR'
            results.append((rel_path, status, arrow))
            print(f'    -> {status}')

        except Exception as e:
            results.append((rel_path, 'ERROR', str(e)[:60]))
            print(f'    -> ERROR: {e}')

    elapsed = time.time() - start_time

    # Summary
    print('\n' + '=' * 60)
    print(f'  BATCH RESULTS')
    print('=' * 60)
    print(f'  {"File":<35} {"Direction":<10} {"Status":<10}')
    print(f'  {"-"*35} {"-"*10} {"-"*10}')
    passed = 0
    failed = 0
    skipped = 0
    for name, status, direction in results:
        status_short = status if len(status) <= 10 else status[:10]
        if status in ('OK', 'PASS'):
            passed += 1
            icon = 'v'
        elif status in ('SKIP', 'COPY'):
            skipped += 1
            icon = '.'
        else:
            failed += 1
            icon = 'x'
        print(f'  {icon} {name:<33} {direction:<10} {status_short:<10}')

    print(f'\n  Total: {len(results)} files | '
          f'{passed} passed | {failed} failed | {skipped} skipped | '
          f'{elapsed:.2f}s')
    print(f'  Output: {output_dir}')

    return results


# ---------------------------------------------------------------------------
def main():
    print(BANNER)
    argv       = sys.argv[1:]
    show_ast   = '--ast'    in argv
    verify     = '--verify' in argv
    demo_mode  = '--demo'   in argv
    to_cpp     = '--to' in argv and 'cpp' in argv

    # Parse --output DIR
    output_dir = None
    if '--output' in argv:
        idx = argv.index('--output')
        if idx + 1 < len(argv):
            output_dir = argv[idx + 1]

    files = [a for a in argv
             if not a.startswith('--') and a not in ('cpp', 'java', 'c')
             and a != output_dir]

    # ── Interactive / demo mode ───────────────────────────────────────────────
    if not files or demo_mode:
        print('No input file given. Running built-in demos.\n')
        print('--- Demo 1: Java -> C ---')
        out = 'demo_output.c'
        run_java_to_c(JAVA_DEMO, out, show_ast=False, verify=verify)
        print('\n--- Demo 2: C -> Java ---')
        with tempfile.NamedTemporaryFile(suffix='.c', mode='w',
                                         encoding='utf-8', delete=False) as tf:
            tf.write(C_DEMO); tmp = tf.name
        run_c_to_java(tmp, 'demo_output.java', show_ast=False)
        os.unlink(tmp)
        return

    path = files[0]
    if not os.path.exists(path):
        print(f'[ERROR] Path not found: {path}'); sys.exit(1)

    # ── Folder batch mode ─────────────────────────────────────────────────────
    if os.path.isdir(path):
        run_batch(path, output_dir, to_cpp, verify, show_ast)
        return

    # ── Single file mode ──────────────────────────────────────────────────────
    ext      = pathlib.Path(path).suffix.lower()
    stem     = pathlib.Path(path).stem

    if ext == '.java':
        with open(path, encoding='utf-8') as f: source = f.read()
        print(f'Input: {path}')
        run_java_to_c(source, stem + '.c', show_ast, verify)

    elif ext == '.c':
        print(f'Input: {path}')
        if to_cpp:
            run_c_to_cpp(path, stem + '.cpp', show_ast, verify)
        else:
            run_c_to_java(path, stem + '.java', show_ast, verify)

    elif ext == '.cpp':
        with open(path, encoding='utf-8') as f: source = f.read()
        print(f'Input: {path}')
        run_cpp_to_c(source, stem + '.c', show_ast, verify)

    else:
        print(f'[ERROR] Unsupported extension "{ext}". Use .java, .c, or .cpp')
        sys.exit(1)


if __name__ == '__main__':
    main()
