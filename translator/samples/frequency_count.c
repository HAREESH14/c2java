// samples/frequency_count.c — frequency count of small-range integers
#include <stdio.h>

int main() {
    int a[] = {1,2,2,3,1,4,2};
    int n = 7;
    int freq[10] = {0};
    for (int i = 0; i < n; ++i) ++freq[a[i]];
    for (int v = 0; v < 10; ++v) if (freq[v]) printf("%d: %d\n", v, freq[v]);
    return 0;
}
