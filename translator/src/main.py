#!/usr/bin/env python3
# =============================================================================
#  main.py  --  Unified C <-> Java Translator
#
#  Usage:
#    uv run python src/main.py input.java          -> Java -> C
#    uv run python src/main.py input.c             -> C   -> Java
#    uv run python src/main.py input.java --verify -> translate + WSL gcc check
#    uv run python src/main.py input.java --ast    -> show javalang AST
#    uv run python src/main.py                     -> interactive mode
# =============================================================================

import sys, os, pathlib, tempfile
sys.path.insert(0, os.path.dirname(__file__))

import java_to_c
import c_to_java
from verify import compile_c_wsl, compile_java_wsl


BANNER = """\
╔══════════════════════════════════════════════╗
║      C  <->  Java  Unified Translator        ║
║   Java parser : javalang                     ║
║   C    parser : pycparser                    ║
╚══════════════════════════════════════════════╝
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
def run_java_to_c(source: str, out_name: str,
                  show_ast: bool, verify: bool):
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
    except ValueError as e:
        print(f'[ERROR] {e}')
        sys.exit(1)

    print('\n[Generated C Code]')
    print(c_code)

    with open(out_name, 'w', encoding='utf-8') as f:
        f.write(c_code)
    print(f'\n[OK] Saved -> {out_name}')

    if verify:
        print('\n[WSL gcc] Compiling generated C...')
        ok, msg = compile_c_wsl(c_code)
        status  = 'PASS' if ok else 'FAIL'
        print(f'  gcc [{status}]: {msg}')
        if not ok:
            sys.exit(2)


def run_c_to_java(path: str, out_name: str, show_ast: bool, verify: bool = False):
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
    except ValueError as e:
        print(f'[ERROR] {e}')
        sys.exit(1)

    print('\n[Generated Java Code]')
    print(java_code)

    with open(out_name, 'w', encoding='utf-8') as f:
        f.write(java_code)
    print(f'\n[OK] Saved -> {out_name}')

    if verify:
        print('\n[WSL javac] Compiling generated Java...')
        ok, msg = compile_java_wsl(java_code)
        status  = 'PASS' if ok else 'FAIL'
        print(f'  javac [{status}]: {msg}')
        if not ok:
            sys.exit(2)


# ---------------------------------------------------------------------------
def main():
    print(BANNER)
    argv       = sys.argv[1:]
    show_ast   = '--ast'    in argv
    verify     = '--verify' in argv
    demo_mode  = '--demo'   in argv
    files      = [a for a in argv if not a.startswith('--')]

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
        print(f'[ERROR] File not found: {path}'); sys.exit(1)

    ext      = pathlib.Path(path).suffix.lower()
    stem     = pathlib.Path(path).stem

    if ext == '.java':
        with open(path, encoding='utf-8') as f: source = f.read()
        print(f'Input: {path}')
        run_java_to_c(source, stem + '.c', show_ast, verify)

    elif ext == '.c':
        print(f'Input: {path}')
        run_c_to_java(path, stem + '.java', show_ast, verify)

    else:
        print(f'[ERROR] Unsupported extension "{ext}". Use .java or .c')
        sys.exit(1)


if __name__ == '__main__':
    main()
