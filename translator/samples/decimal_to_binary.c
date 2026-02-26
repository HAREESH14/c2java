// samples/decimal_to_binary.c — Convert integers to binary string (no pointers)
#include <stdio.h>

void to_binary(int x, char out[], int width) {
    for (int i = width-1; i >= 0; --i) {
        out[i] = (x & 1) ? '1' : '0';
        x >>= 1;
    }
    out[width] = '\0';
}

int main() {
    int nums[] = {5, 10, 255, 102};
    int n = 4;
    char buf[16];
    for (int i = 0; i < n; ++i) {
        to_binary(nums[i], buf, 8);
        printf("%d -> %s\n", nums[i], buf);
    }
    return 0;
}

/* Expected output:
5 -> 00000101
10 -> 00001010
255 -> 11111111
102 -> 01100110
*/