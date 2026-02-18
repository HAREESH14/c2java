// test9_casting_prefix.c
// Tests: type casting, prefix ++/--, global variables
#include <stdio.h>

int counter = 0;
float ratio = 0.5;

int main() {
    // Type casting
    int n = 7;
    float result = (float)n / 2;
    printf("Cast result: %f\n", result);

    int total = (int)3.99;
    printf("Int cast: %d\n", total);

    // Prefix ++ and --
    int i = 5;
    ++i;
    printf("After ++i: %d\n", i);
    --i;
    printf("After --i: %d\n", i);

    // Prefix in expression
    int j = 3;
    int k = ++j + 1;
    printf("k = %d\n", k);

    // Global variable access
    counter = counter + 1;
    printf("counter = %d\n", counter);
    printf("ratio = %f\n", ratio);

    return 0;
}
