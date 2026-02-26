// samples/is_prime_batch.c — Check primality for a list of numbers
#include <stdio.h>
#include <math.h>

int is_prime(int n) {
    if (n <= 1) return 0;
    if (n <= 3) return 1;
    if (n % 2 == 0) return 0;
    int r = (int)sqrt(n);
    for (int i = 3; i <= r; i += 2) if (n % i == 0) return 0;
    return 1;
}

int main() {
    int nums[] = {2, 3, 4, 16, 17, 19, 20, 23, 29};
    int n = 9;
    for (int i = 0; i < n; ++i) {
        printf("%d -> %s\n", nums[i], is_prime(nums[i]) ? "PRIME" : "COMPOSITE");
    }
    return 0;
}

/* Expected output:
2 -> PRIME
3 -> PRIME
4 -> COMPOSITE
16 -> COMPOSITE
17 -> PRIME
19 -> PRIME
20 -> COMPOSITE
23 -> PRIME
29 -> PRIME
*/