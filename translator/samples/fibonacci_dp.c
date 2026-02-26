// samples/fibonacci_dp.c — compute Fibonacci numbers with iterative DP
#include <stdio.h>

int main() {
    int n = 20;
    long long f[100];
    f[0] = 0; f[1] = 1;
    for (int i = 2; i <= n; ++i) f[i] = f[i-1] + f[i-2];
    for (int i = 0; i <= n; ++i) printf("%d: %lld\n", i, f[i]);
    return 0;
}
