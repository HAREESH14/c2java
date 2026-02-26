// samples/fast_power.c — fast exponentiation (iterative)
#include <stdio.h>

long long fast_pow(long long base, long long exp) {
    long long result = 1;
    long long b = base;
    while (exp > 0) {
        if (exp & 1) result *= b;
        b *= b;
        exp >>= 1;
    }
    return result;
}

int main() {
    long long b = 3, e = 13;
    printf("%lld^%lld = %lld\n", b, e, fast_pow(b,e));
    return 0;
}
