// test11_struct.c
// Tests: struct definition, struct variable declaration, member access/assignment
#include <stdio.h>

struct Point {
    int x;
    int y;
};

struct Rectangle {
    int width;
    int height;
};

int area(int w, int h) {
    return w * h;
}

int main() {
    // Struct variable declaration
    struct Point p;
    p.x = 3;
    p.y = 4;
    printf("Point: (%d, %d)\n", p.x, p.y);

    // Struct with initializer
    struct Point q = {10, 20};
    printf("Q: (%d, %d)\n", q.x, q.y);

    // Struct member in expression
    int dist;
    dist = p.x + p.y;
    printf("dist = %d\n", dist);

    // Rectangle
    struct Rectangle r;
    r.width = 5;
    r.height = 8;
    int a;
    a = area(r.width, r.height);
    printf("Area = %d\n", a);

    return 0;
}
