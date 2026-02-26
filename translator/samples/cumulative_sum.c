// samples/cumulative_sum.c — prefix sums (cumulative sum)
#include <stdio.h>

int main() {
    int a[] = {1,2,3,4,5};
    int n = 5;
    int pref[100];
    pref[0] = a[0];
    for (int i = 1; i < n; ++i) pref[i] = pref[i-1] + a[i];
    for (int i = 0; i < n; ++i) printf("%d ", pref[i]);
    printf("\n");
    return 0;
}
