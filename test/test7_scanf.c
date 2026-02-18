// test7_scanf.c
// Tests scanf (user input) and ternary operator
#include <stdio.h>

int main() {
    int n;
    printf("Enter a number: \n");
    scanf("%d", &n);

    // ternary operator
    int abs_val = (n >= 0) ? n : -n;
    printf("Absolute value: %d\n", abs_val);

    // even or odd using ternary
    printf("Even or odd: \n");
    int is_even = (n % 2 == 0) ? 1 : 0;
    if (is_even) {
        printf("Even\n");
    } else {
        printf("Odd\n");
    }

    // read two numbers and print sum
    int a;
    int b;
    scanf("%d", &a);
    scanf("%d", &b);
    printf("Sum: %d\n", a + b);

    return 0;
}
