#include <stdio.h>

int add(int a, int b);
int factorial(int n);

int add(int a, int b) {
    return (a + b);
}

int factorial(int n) {
    if ((n <= 1)) {
        return 1;
    }
    return (n * factorial((n - 1)));
}

int main() {
    int x = 5;
    int y = 3;
    int sum = add(x, y);
    printf("Sum: %d\n", sum);
    for (/* expr:VariableDeclaration */; (i <= 5); i++) {
        printf("%d\n", i);
    }
    int n = 5;
    int fact = factorial(n);
    printf("Factorial of %d = %d\n", n, fact);
    if ((x > y)) {
        printf("x is greater\n");
    } else {
        printf("y is greater\n");
    }
    return 0;
}