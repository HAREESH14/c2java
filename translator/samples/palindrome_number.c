// samples/palindrome_number.c — Check numeric palindromes in a list
#include <stdio.h>

int is_palnum(int x) {
    int orig = x, rev = 0;
    while (x > 0) {
        rev = rev * 10 + (x % 10);
        x /= 10;
    }
    return rev == orig;
}

int main() {
    int tests[] = {121, 12321, 4554, 123, 10};
    int n = 5;
    for (int i = 0; i < n; ++i) {
        int v = tests[i];
        printf("%d -> %s\n", v, is_palnum(v) ? "PALINDROME" : "NOT");
    }
    return 0;
}

/* Expected output:
121 -> PALINDROME
12321 -> PALINDROME
4554 -> PALINDROME
123 -> NOT
10 -> NOT
*/