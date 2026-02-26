// samples/factorial_tail_recursive.c — factorial using tail recursion
#include <stdio.h>

long long fact_tail(int n, long long acc) {
    if (n <= 1) return acc;
    return fact_tail(n-1, acc * n);
}

int main() {
    int n = 10;
    printf("%d! = %lld\n", n, fact_tail(n, 1));
    return 0;
}
