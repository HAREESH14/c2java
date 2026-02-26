// samples/digit_product.c — product of digits of a positive integer
#include <stdio.h>

int main() {
    int n = 2345;
    int prod = 1;
    while (n > 0) { prod *= (n % 10); n /= 10; }
    printf("Product of digits: %d\n", prod);
    return 0;
}
