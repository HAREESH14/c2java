// samples/reverse_string.c — Reverse a string in-place
#include <stdio.h>
#include <string.h>

void reverse(char *s) {
    int i = 0, j = strlen(s)-1;
    while (i < j) {
        char t = s[i]; s[i] = s[j]; s[j] = t;
        i++; j--;
    }
}

int main() {
    char s1[] = "hello";
    char s2[] = "OpenAI";
    printf("%s -> ", s1); reverse(s1); printf("%s\n", s1);
    printf("%s -> ", s2); reverse(s2); printf("%s\n", s2);
    return 0;
}

/* Expected output:
hello -> olleh
OpenAI -> IAnepO
*/