// samples/count_primes_range.c — count primes in a range [2..n]
#include <stdio.h>
#include <math.h>

int is_prime(int x) {
    if (x < 2) return 0;
    for (int i = 2; i*i <= x; ++i) if (x % i == 0) return 0;
    return 1;
}

int main() {
    int n = 100;
    int count = 0;
    for (int i = 2; i <= n; ++i) if (is_prime(i)) ++count;
    printf("Primes up to %d: %d\n", n, count);
    return 0;
}
