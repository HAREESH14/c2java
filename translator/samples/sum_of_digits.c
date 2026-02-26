// samples/sum_of_digits.c — sum digits of a positive integer
#include <stdio.h>

int main() {
    int n = 123456;
    int s = 0;
    while (n > 0) { s += n % 10; n /= 10; }
    printf("Sum of digits: %d\n", s);
    return 0;
}
