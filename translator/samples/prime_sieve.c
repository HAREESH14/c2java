// samples/prime_sieve.c — Sieve of Eratosthenes
#include <stdio.h>
#include <string.h>

void sieve(int n) {
    int is_prime[1000];
    for (int i = 0; i <= n; ++i) is_prime[i] = 1;
    is_prime[0] = is_prime[1] = 0;
    for (int p = 2; p * p <= n; ++p) {
        if (is_prime[p]) {
            for (int multiple = p * p; multiple <= n; multiple += p) is_prime[multiple] = 0;
        }
    }
    for (int i = 2; i <= n; ++i) if (is_prime[i]) printf("%d ", i);
    printf("\n");
}

int main() {
    int n = 50;
    sieve(n);
    return 0;
}
