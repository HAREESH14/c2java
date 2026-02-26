// samples/palindrome_check.c — Check palindromes with test strings
#include <stdio.h>
#include <string.h>

int is_palindrome(const char *s) {
    int i = 0, j = strlen(s)-1;
    while (i < j) {
        if (s[i] != s[j]) return 0;
        i++; j--;
    }
    return 1;
}

int main() {
    const char *tests[] = {"radar", "level", "hello", "world"};
    for (int i = 0; i < 4; ++i) {
        printf("%s -> %s\n", tests[i], is_palindrome(tests[i]) ? "PALINDROME" : "NOT");
    }
    return 0;
}

/* Expected output:
radar -> PALINDROME
level -> PALINDROME
hello -> NOT
world -> NOT
*/