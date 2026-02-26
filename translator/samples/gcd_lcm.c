// samples/gcd_lcm.c — compute GCD and LCM of two numbers
#include <stdio.h>

int gcd(int a, int b) {
    if (a < 0) a = -a; if (b < 0) b = -b;
    while (b != 0) {
        int t = b;
        b = a % b;
        a = t;
    }
    return a;
}

int lcm(int a, int b) {
    int g = gcd(a, b);
    if (g == 0) return 0;
    return (a / g) * b;
}

int main() {
    int x = 48, y = 180;
    printf("Numbers: %d, %d\n", x, y);
    printf("GCD: %d\n", gcd(x,y));
    printf("LCM: %d\n", lcm(x,y));
    return 0;
}
