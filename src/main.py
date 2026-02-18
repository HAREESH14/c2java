#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
#  main.py  —  C to Java Translator
#  Pure Python. No external libraries n'New folder'eeded.
#
#  USAGE:
#    python3 main.py input.c              → translates input.c → Main.java
#    python3 main.py input.c --ast        → also prints the AST tree
#    python3 main.py input.c --tokens     → also prints all tokens
#    python3 main.py                      → runs built-in demo
# ─────────────────────────────────────────────────────────────────────────────

import sys
import os

# Add src/ to path
sys.path.insert(0, os.path.dirname(__file__))

from lexer       import Lexer
from parser      import Parser
from visitor     import CToJavaVisitor
from ast_printer import ASTPrinter


# ── Built-in demo program ─────────────────────────────────────────────────────
DEMO = r"""
int add(int a, int b) {
    return a + b;
}

int max(int a, int b) {
    if (a > b) {
        return a;
    } else {
        return b;
    }
}

void printArray(int arr[], int size) {
    for (int i = 0; i < size; i++) {
        printf("%d", arr[i]);
    }
}

int main() {
    /* Variables */
    int x = 10;
    int y = 20;
    float pi = 3.14;

    /* Function calls */
    int result = add(x, y);
    printf("Sum: %d\n", result);

    /* if/else */
    if (x < y) {
        printf("x is smaller\n");
    } else {
        printf("y is smaller\n");
    }

    /* for loop */
    for (int i = 0; i < 5; i++) {
        printf("%d", i);
    }

    /* while loop */
    int n = 1;
    while (n <= 3) {
        printf("%d", n);
        n = n + 1;
    }

    /* do-while loop */
    int count = 3;
    do {
        printf("%d", count);
        count = count - 1;
    } while (count > 0);

    /* 1D Array with size */
    int scores[5];
    scores[0] = 90;
    scores[1] = 85;
    scores[2] = 78;
    scores[3] = 92;
    scores[4] = 88;

    /* 1D Array with initializer */
    int primes[] = {2, 3, 5, 7, 11};

    /* Array access in loop */
    for (int i = 0; i < 5; i++) {
        printf("%d", primes[i]);
    }

    /* 2D Array */
    int matrix[3][3];
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            matrix[i][j] = i + j;
        }
    }

    return 0;
}
"""


def translate(source, show_tokens=False, show_ast=False):
    print('=' * 55)
    print('  C → JAVA TRANSLATOR  (Pure Python)')
    print('=' * 55)

    # ── Step 1: Lex ───────────────────────────────────────────────────────
    lexer  = Lexer(source)
    tokens = lexer.tokenize()

    if show_tokens:
        print('\n── TOKENS ──────────────────────────────────────────')
        for tok in tokens:
            print(f'  {tok.type:<12} {tok.value!r}')

    # ── Step 2: Parse → AST ───────────────────────────────────────────────
    parser = Parser(tokens)
    ast    = parser.parse()

    if show_ast:
        print('\n── AST TREE ─────────────────────────────────────────')
        printer = ASTPrinter()
        print(printer.get_tree(ast))

    # ── Step 3: Visit AST → emit Java ─────────────────────────────────────
    visitor   = CToJavaVisitor()
    java_code = visitor.visit(ast)

    print('\n── GENERATED JAVA CODE ──────────────────────────────')
    print(java_code)

    return java_code


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
    else:
        print('No file given — using built-in demo program.')
        source = DEMO

    java_code = translate(source, show_tokens=show_tokens, show_ast=show_ast)

    # Save output
    output_path = 'Main.java'
    with open(output_path, 'w') as f:
        f.write(java_code)
    print(f'\n✓ Saved to {output_path}')


if __name__ == '__main__':
    main()
