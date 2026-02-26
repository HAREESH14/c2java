// samples/factorial_recursive.c — Recursive factorial with test data
#include <stdio.h>

long fact(int n) {
    if (n <= 1) return 1;
    return n * fact(n-1);
}

int main() {
    int values[] = {0,1,5,10};
    int n = 4;
    for (int i=0;i<n;i++) printf("%d! = %ld\n", values[i], fact(values[i]));
    return 0;
}

/* Expected output:
0! = 1
1! = 1
5! = 120
10! = 3628800
*/