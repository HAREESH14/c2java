// samples/trailing_zero_factorial.c — count trailing zeros in n! (by factors of 5)
#include <stdio.h>

int trailing_zeros(int n) {
    int count = 0;
    for (int i = 5; i <= n; i *= 5) count += n / i;
    return count;
}

int main() {
    int n = 100;
    printf("Trailing zeros in %d! = %d\n", n, trailing_zeros(n));
    return 0;
}
