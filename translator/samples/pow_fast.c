// samples/pow_fast.c — Fast exponentiation (binary exponentiation) with test data
#include <stdio.h>

long pow_fast(long base, int exp) {
    long res = 1;
    while (exp > 0) {
        if (exp & 1) res *= base;
        base *= base;
        exp >>= 1;
    }
    return res;
}

int main() {
    printf("2^10 = %ld\n", pow_fast(2,10));
    printf("3^7  = %ld\n", pow_fast(3,7));
    printf("5^0  = %ld\n", pow_fast(5,0));
    return 0;
}

/* Expected output:
2^10 = 1024
3^7  = 2187
5^0  = 1
*/