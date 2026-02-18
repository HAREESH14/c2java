// test8_multivar_define.c
// Tests: #define constants, multi-variable declaration
#include <stdio.h>
#define MAX 100
#define PI 3.14159

int main() {
    // Multi-variable declaration
    int a, b, c;
    a = 10;
    b = 20;
    c = a + b;

    // Multi-var with initializer
    int x = 5, y = 10, z = 15;

    printf("c = %d\n", c);
    printf("MAX = %d\n", MAX);
    printf("PI = %f\n", PI);
    printf("x + y + z = %d\n", x + y + z);

    return 0;
}
