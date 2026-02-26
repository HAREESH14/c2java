// samples/find_second_largest.c — find second largest element in an array
#include <stdio.h>

int main() {
    int a[] = {5, 3, 9, 1, 6, 9};
    int n = 6;
    int max = a[0], second = a[0];
    for (int i = 1; i < n; ++i) {
        if (a[i] > max) { second = max; max = a[i]; }
        else if (a[i] > second && a[i] < max) second = a[i];
    }
    printf("Max: %d, Second max: %d\n", max, second);
    return 0;
}
