// samples/is_prime_simple.c — check primality of a single number
#include <stdio.h>
#include <math.h>

int main() {
    int n = 37;
    if (n < 2) { printf("Not prime\n"); return 0; }
    for (int i = 2; i <= (int)sqrt(n); ++i) if (n % i == 0) { printf("Not prime\n"); return 0; }
    printf("Prime\n");
    return 0;
}
