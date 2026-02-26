// samples/merge_sort.c — Merge sort (array-based, recursive) with test data
#include <stdio.h>

void merge(int a[], int l, int m, int r) {
    int n1 = m - l + 1;
    int n2 = r - m;
    int L[50], R[50]; // fixed-size local buffers for small educational examples
    for (int i = 0; i < n1; i++) L[i] = a[l + i];
    for (int j = 0; j < n2; j++) R[j] = a[m + 1 + j];
    int i = 0, j = 0, k = l;
    while (i < n1 && j < n2) {
        if (L[i] <= R[j]) a[k++] = L[i++]; else a[k++] = R[j++];
    }
    while (i < n1) a[k++] = L[i++];
    while (j < n2) a[k++] = R[j++];
}

void merge_sort(int a[], int l, int r) {
    if (l < r) {
        int m = (l + r) / 2;
        merge_sort(a, l, m);
        merge_sort(a, m+1, r);
        merge(a, l, m, r);
    }
}

void print_array(int a[], int n) {
    for (int i = 0; i < n; ++i) printf("%d ", a[i]);
    printf("\n");
}

int main() {
    int data[] = {38, 27, 43, 3, 9, 82, 10};
    int n = 7;
    printf("Original: "); print_array(data, n);
    merge_sort(data, 0, n-1);
    printf("Sorted:   "); print_array(data, n);
    return 0;
}

/* Expected output:
Original: 38 27 43 3 9 82 10 
Sorted:   3 9 10 27 38 43 82 
*/