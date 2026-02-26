// samples/gcd_euclid.c — Euclidean GCD with test pairs
#include <stdio.h>

int gcd(int a, int b) {
    if (b == 0) return a >= 0 ? a : -a;
    return gcd(b, a % b);
}

int main() {
    int a = 48, b = 18;
    printf("GCD of %d and %d is %d\n", a, b, gcd(a,b));
    a = 270; b = 192;
    printf("GCD of %d and %d is %d\n", a, b, gcd(a,b));
    return 0;
}

/* Expected output:
GCD of 48 and 18 is 6
GCD of 270 and 192 is 6
*/