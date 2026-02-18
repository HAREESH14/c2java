// test10_strings.c
// Tests: string functions, math functions, character functions, conversion
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <ctype.h>
#include <stdlib.h>

int main() {
    // ── strlen ──────────────────────────────────────────────────────────────
    int len;
    len = strlen("Hello");
    printf("strlen: %d\n", len);

    // ── strcmp ──────────────────────────────────────────────────────────────
    int cmp;
    cmp = strcmp("abc", "abc");
    printf("strcmp equal: %d\n", cmp);

    // ── toupper / tolower ────────────────────────────────────────────────────
    char ch = 'a';
    char up;
    up = toupper(ch);
    printf("toupper: %c\n", up);

    char lo;
    lo = tolower('Z');
    printf("tolower: %c\n", lo);

    // ── isalpha / isdigit ────────────────────────────────────────────────────
    int alpha;
    alpha = isalpha('A');
    printf("isalpha A: %d\n", alpha);

    int digit;
    digit = isdigit('5');
    printf("isdigit 5: %d\n", digit);

    // ── atoi / atof ──────────────────────────────────────────────────────────
    int num;
    num = atoi("42");
    printf("atoi: %d\n", num);

    double dnum;
    dnum = atof("3.14");
    printf("atof: %f\n", dnum);

    // ── math functions ───────────────────────────────────────────────────────
    double sq;
    sq = sqrt(16.0);
    printf("sqrt(16): %f\n", sq);

    double pw;
    pw = pow(2.0, 8.0);
    printf("pow(2,8): %f\n", pw);

    double ab;
    ab = fabs(-5.5);
    printf("fabs(-5.5): %f\n", ab);

    // ── rand ─────────────────────────────────────────────────────────────────
    int r;
    r = rand();
    printf("rand: %d\n", r);

    return 0;
}
