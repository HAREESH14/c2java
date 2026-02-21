#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
#  main.py  —  Java → C Translator
#
#  External library used: pycparser  (pip install pycparser)
#  pycparser is used to: build C AST nodes and emit valid C source code.
#
#  USAGE:
#    python3 main.py input.java           → translates to output.c
#    python3 main.py input.java --ast     → also prints Java AST
#    python3 main.py input.java --tokens  → also prints Java tokens
#    python3 main.py                      → runs built-in demo
# ─────────────────────────────────────────────────────────────────────────────

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from java_lexer        import JavaLexer
from java_parser       import JavaParser
from java_to_c_visitor import JavaToCVisitor


DEMO = """
public class Main {

    public static int add(int a, int b) {
        return a + b;
    }

    public static int max(int a, int b) {
        if (a > b) {
            return a;
        } else {
            return b;
        }
    }

    public static void printArray(int[] arr, int size) {
        for (int i = 0; i < size; i++) {
            System.out.println(arr[i]);
        }
    }

    public static void main(String[] args) {
        int x = 10;
        int y = 20;
        float pi = 3.14f;

        int result = add(x, y);
        System.out.printf("Sum: %d%n", result);

        if (x < y) {
            System.out.println("x is smaller");
        } else if (x == y) {
            System.out.println("equal");
        } else {
            System.out.println("y is smaller");
        }

        for (int i = 0; i < 5; i++) {
            System.out.println(i);
        }

        int n = 1;
        while (n <= 3) {
            System.out.println(n);
            n = n + 1;
        }

        int count = 3;
        do {
            System.out.println(count);
            count = count - 1;
        } while (count > 0);

        int[] scores = new int[5];
        scores[0] = 90;
        scores[1] = 85;
        scores[2] = 78;
        scores[3] = 92;
        scores[4] = 88;

        int[] primes = {2, 3, 5, 7, 11};

        for (int i = 0; i < 5; i++) {
            System.out.println(primes[i]);
        }

        int[][] matrix = new int[3][3];
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3; j++) {
                matrix[i][j] = i + j;
            }
        }

        printArray(scores, 5);
    }
}
"""


def translate(source, show_tokens=False, show_ast=False):
    print('=' * 58)
    print('  JAVA → C TRANSLATOR  (pycparser backend)')
    print('=' * 58)

    # ── Step 1: Lex ───────────────────────────────────────────────────────
    lexer  = JavaLexer(source)
    tokens = lexer.tokenize()

    if show_tokens:
        print('\n── TOKENS ──────────────────────────────────────────────')
        for tok in tokens:
            print(f'  {tok.type:<14} {tok.value!r}')

    # ── Step 2: Parse Java → Java AST ────────────────────────────────────
    parser   = JavaParser(tokens)
    java_ast = parser.parse()

    if show_ast:
        print('\n── JAVA AST ─────────────────────────────────────────────')
        print(f'  Class: {java_ast.class_name}')
        for method in java_ast.methods:
            tag = '[main]' if method.is_main else ''
            print(f'  Method: {method.return_type} {method.name}() {tag}')
            print(f'    Params: {[(p.type_, p.name) for p in method.params]}')
            print(f'    Statements: {len(method.body.statements)}')
            for stmt in method.body.statements:
                print(f'      {type(stmt).__name__}')

    # ── Step 3: Visit Java AST → Build C AST → Emit C (via pycparser) ────
    visitor = JavaToCVisitor()
    c_code  = visitor.visit(java_ast)

    print('\n── GENERATED C CODE ─────────────────────────────────────')
    print(c_code)

    return c_code


def main():
    args        = sys.argv[1:]
    show_tokens = '--tokens' in args
    show_ast    = '--ast'    in args
    files       = [a for a in args if not a.startswith('--')]

    if files:
        path = files[0]
        if not os.path.exists(path):
            print(f'Error: File not found: {path}')
            sys.exit(1)
        with open(path) as f:
            source = f.read()
        print(f'Translating: {path}')
        out_name = os.path.splitext(os.path.basename(path))[0] + '.c'
    else:
        print('No file given — using built-in demo.')
        source   = DEMO
        out_name = 'output.c'

    c_code = translate(source, show_tokens=show_tokens, show_ast=show_ast)

    with open(out_name, 'w') as f:
        f.write(c_code)
    print(f'\n✓ Saved to {out_name}')


if __name__ == '__main__':
    main()
