#!/usr/bin/env python3
"""Explore libclang Cursor tree for a simple C program."""
import sys, os, tempfile
import clang.cindex as ci

SRC = r'''
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

struct Point { int x; int y; };

int is_prime(int n) {
    if (n <= 1) return 0;
    for (int i = 2; i * i <= n; i++)
        if (n % i == 0) return 0;
    return 1;
}

void reverse(char *s, int len) {
    for (int i = 0; i < len / 2; i++) {
        char t = s[i];
        s[i] = s[len - 1 - i];
        s[len - 1 - i] = t;
    }
}

int main() {
    int *p = (int*)malloc(sizeof(int));
    *p = 42;
    printf("%d\n", *p);
    free(p);

    struct Point pt;
    pt.x = 10;

    char buf[100];
    buf[0] = 'A';

    char *name = "hello";

    if (is_prime(7)) {
        printf("prime\n");
    }

    double x = sqrt(3.14);
    return 0;
}
'''

def dump(cursor, indent=0):
    kind = cursor.kind.name
    spelling = cursor.spelling or ''
    typ = cursor.type.spelling if cursor.type else ''
    loc = ''
    if cursor.location and cursor.location.file:
        loc = f' L{cursor.location.line}'
    # Only show nodes from our file (skip stdlib headers)
    if cursor.location.file and '/tmp/' in (cursor.location.file.name or ''):
        print(f"{'  ' * indent}{kind} '{spelling}' type='{typ}'{loc}")
    for child in cursor.get_children():
        dump(child, indent + 1 if (cursor.location.file and '/tmp/' in (cursor.location.file.name or '')) else indent)

def main():
    with tempfile.NamedTemporaryFile(suffix='.c', mode='w', delete=False, dir='/tmp') as f:
        f.write(SRC)
        tmp = f.name

    index = ci.Index.create()
    tu = index.parse(tmp, args=['-std=c11'])
    
    # Show diagnostics
    for d in tu.diagnostics:
        print(f"DIAG: {d.severity} {d.spelling}")
    
    print("\n=== AST DUMP ===\n")
    dump(tu.cursor)
    os.unlink(tmp)

if __name__ == '__main__':
    main()
