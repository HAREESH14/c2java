// samples/simple_statistics.c — sum, average, min, max
#include <stdio.h>

int main() {
    int a[] = {5, 3, 9, 1, 6};
    int n = 5;
    int sum = 0, min = a[0], max = a[0];
    for (int i = 0; i < n; ++i) {
        sum += a[i];
        if (a[i] < min) min = a[i];
        if (a[i] > max) max = a[i];
    }
    printf("Array: "); for (int i=0;i<n;i++) printf("%d ", a[i]); printf("\n");
    printf("Sum: %d\n", sum);
    printf("Avg: %.2f\n", (double)sum/n);
    printf("Min: %d\n", min);
    printf("Max: %d\n", max);
    return 0;
}
