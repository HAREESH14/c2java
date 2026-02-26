// samples/rotate_array.c — rotate array right by k positions
#include <stdio.h>

void rotate_right(int a[], int n, int k) {
    k %= n;
    int b[100];
    for (int i = 0; i < n; ++i) b[(i+k)%n] = a[i];
    for (int i = 0; i < n; ++i) a[i] = b[i];
}

int main() {
    int a[] = {1,2,3,4,5};
    int n = 5, k = 2;
    rotate_right(a, n, k);
    for (int i = 0; i < n; ++i) printf("%d ", a[i]);
    printf("\n");
    return 0;
}
