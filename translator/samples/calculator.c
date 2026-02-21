// samples/calculator.c -- C calculator with scanf, switch, functions
#include <stdio.h>

float add(float a, float b) { return a + b; }
float sub(float a, float b) { return a - b; }
float mul(float a, float b) { return a * b; }
float divide(float a, float b) { return b != 0 ? a / b : 0; }

int main() {
    float a, b, result;
    int op;

    printf("Enter two numbers: ");
    scanf("%f %f", &a, &b);

    printf("Choose: 1=add 2=sub 3=mul 4=div: ");
    scanf("%d", &op);

    switch (op) {
        case 1: result = add(a, b);    break;
        case 2: result = sub(a, b);    break;
        case 3: result = mul(a, b);    break;
        case 4: result = divide(a, b); break;
        default: result = 0;           break;
    }

    printf("Result: %f\n", result);

    int i;
    for (i = 1; i <= 5; i++) {
        if (i == 3) continue;
        printf("i = %d\n", i);
    }
    return 0;
}
