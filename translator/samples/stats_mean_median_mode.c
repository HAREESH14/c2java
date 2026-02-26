// samples/stats_mean_median_mode.c — Compute mean, median, and mode for small array
#include <stdio.h>

void sort(int a[], int n) {
    for (int i = 0; i < n-1; ++i)
        for (int j = 0; j < n-i-1; ++j)
            if (a[j] > a[j+1]) { int t=a[j]; a[j]=a[j+1]; a[j+1]=t; }
}

float mean(int a[], int n) {
    int s = 0;
    for (int i = 0; i < n; ++i) s += a[i];
    return ((float)s)/n;
}

float median(int a[], int n) {
    int b[50];
    for (int i = 0; i < n; ++i) b[i] = a[i];
    sort(b, n);
    if (n % 2 == 1) return b[n/2];
    return (b[n/2 - 1] + b[n/2]) / 2.0f;
}

int mode(int a[], int n) {
    int best = a[0], best_count = 1;
    for (int i = 0; i < n; ++i) {
        int cnt = 1;
        for (int j = i+1; j < n; ++j) if (a[j] == a[i]) ++cnt;
        if (cnt > best_count) { best_count = cnt; best = a[i]; }
    }
    return best;
}

int main() {
    int data[] = {1,2,2,3,4,2,5};
    int n = 7;
    printf("Data: "); for (int i=0;i<n;i++) printf("%d ", data[i]); printf("\n");
    printf("Mean: %.2f\n", mean(data,n));
    printf("Median: %.2f\n", median(data,n));
    printf("Mode: %d\n", mode(data,n));
    return 0;
}

/* Expected output:
Data: 1 2 2 3 4 2 5 
Mean: 2.43
Median: 2.00
Mode: 2
*/