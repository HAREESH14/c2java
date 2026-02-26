// samples/sieve_eratosthenes.c — Sieve of Eratosthenes up to N
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main() {
    int N = 30;
    char *is_prime = malloc(N+1);
    memset(is_prime, 1, N+1);
    is_prime[0] = is_prime[1] = 0;
    for (int p = 2; p*p <= N; ++p) {
        if (is_prime[p]) {
            for (int k = p*p; k <= N; k += p) is_prime[k] = 0;
        }
    }
    printf("Primes up to %d:\n", N);
    for (int i = 2; i <= N; ++i) if (is_prime[i]) printf("%d ", i);
    printf("\n");
    free(is_prime);
    return 0;
}

/* Expected output:
Primes up to 30:
2 3 5 7 11 13 17 19 23 29 
*/