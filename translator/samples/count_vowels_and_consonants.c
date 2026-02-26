// samples/count_vowels_and_consonants.c — Count vowels and consonants in a string
#include <stdio.h>
#include <ctype.h>

int main() {
    char s[] = "Hello World";
    int vowels = 0, consonants = 0;
    for (int i = 0; s[i] != '\0'; ++i) {
        char c = tolower(s[i]);
        if (c >= 'a' && c <= 'z') {
            if (c=='a' || c=='e' || c=='i' || c=='o' || c=='u') ++vowels;
            else ++consonants;
        }
    }
    printf("String: %s\n", s);
    printf("Vowels: %d, Consonants: %d\n", vowels, consonants);
    return 0;
}
