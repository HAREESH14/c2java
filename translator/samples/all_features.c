// samples/all_features.c — comprehensive C test of all supported features
#include <stdio.h>
#include <string.h>
#include <math.h>

int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}

int max(int a, int b) {
    return a > b ? a : b;
}

float average(float a, float b) {
    return (a + b) / 2.0f;
}

void print_array(int arr[], int size) {
    int i;
    for (i = 0; i < size; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");
}

int main() {
    // Variables
    int x = 10;
    float pi = 3.14f;
    double e = 2.718;
    char ch = 'A';
    long big = 999999;
    short small_val = 5;

    // Compound assignments
    x += 5;
    x -= 2;
    x *= 3;
    x /= 4;
    printf("x = %d\n", x);

    // Prefix / postfix
    int a = 3;
    a++;
    ++a;
    a--;
    --a;

    // if / else if / else
    if (x > 100) {
        printf("big\n");
    } else if (x > 10) {
        printf("medium\n");
    } else {
        printf("small\n");
    }

    // for loop
    int sum = 0;
    int i;
    for (i = 1; i <= 10; i++) {
        sum += i;
    }
    printf("sum = %d\n", sum);

    // while
    int count = 0;
    while (count < 5) {
        count++;
    }

    // do-while
    int n = 10;
    do {
        n -= 3;
    } while (n > 0);
    printf("n = %d\n", n);

    // break / continue
    for (i = 0; i < 20; i++) {
        if (i % 2 == 0) continue;
        if (i > 9) break;
        printf("%d\n", i);
    }

    // Arrays
    int arr[5] = {10, 20, 30, 40, 50};
    int fib[] = {1, 1, 2, 3, 5, 8};
    arr[0] = 99;
    print_array(arr, 5);
    print_array(fib, 6);

    // Switch
    int day = 3;
    switch (day) {
        case 1: printf("Mon\n"); break;
        case 2: printf("Tue\n"); break;
        case 3: printf("Wed\n"); break;
        default: printf("Other\n"); break;
    }

    // Function calls
    int result = factorial(5);
    printf("5! = %d\n", result);
    printf("max = %d\n", max(42, 17));

    // String functions
    char name[] = "Hello";
    int len = strlen(name);
    printf("len = %d\n", len);

    // Math functions
    double sq = sqrt(16.0);
    printf("sqrt(16) = %f\n", sq);

    // Ternary
    int abs_x = x > 0 ? x : -x;
    printf("abs = %d\n", abs_x);

    // scanf
    int user_input;
    printf("Enter a number: ");
    scanf("%d", &user_input);
    printf("You entered: %d\n", user_input);

    return 0;
}
