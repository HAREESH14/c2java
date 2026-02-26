// samples/armstrong_numbers.c — Test list for Armstrong (narcissistic) numbers
#include <stdio.h>
#include <math.h>

int is_armstrong(int x) {
    int original = x, sum = 0;
    int digits = 0, t = x;
    while (t) { digits++; t /= 10; }
    t = x;
    while (t) {
        int d = t % 10;
        int p = (int)pow(d, digits);
        sum += p;
        t /= 10;
    }
    return sum == original;
}

int main() {
    int tests[] = {153, 370, 371, 9474, 9475, 123};
    int n = 6;
    for (int i = 0; i < n; ++i) {
        int v = tests[i];
        printf("%d -> %s\n", v, is_armstrong(v) ? "ARMSTRONG" : "NOT");
    }
    return 0;
}

/* Expected output:
153 -> ARMSTRONG
370 -> ARMSTRONG
371 -> ARMSTRONG
9474 -> ARMSTRONG
9475 -> NOT
123 -> NOT
*/