// samples/kadane_max_subarray.c — maximum subarray sum (Kadane's algorithm)
#include <stdio.h>

int main() {
    int a[] = {-2, 1, -3, 4, -1, 2, 1, -5, 4};
    int n = 9;
    int max_ending = a[0], max_so_far = a[0];
    for (int i = 1; i < n; ++i) {
        if (max_ending < 0) max_ending = a[i]; else max_ending += a[i];
        if (max_ending > max_so_far) max_so_far = max_ending;
    }
    printf("Max subarray sum: %d\n", max_so_far);
    return 0;
}
