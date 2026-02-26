// samples/quick_sort.c — Quick sort (in-place index swap) with test data
#include <stdio.h>

void swap(int a[], int i, int j) {
    int t = a[i]; a[i] = a[j]; a[j] = t;
}

int partition(int a[], int low, int high) {
    int pivot = a[high];
    int i = low - 1;
    for (int j = low; j <= high - 1; j++) {
        if (a[j] < pivot) { i++; swap(a, i, j); }
    }
    swap(a, i+1, high);
    return i+1;
}

void quick_sort(int a[], int low, int high) {
    if (low < high) {
        int pi = partition(a, low, high);
        quick_sort(a, low, pi - 1);
        quick_sort(a, pi + 1, high);
    }
}

void print_array(int a[], int n) { for (int i=0;i<n;i++) printf("%d ", a[i]); printf("\n"); }

int main() {
    int arr[] = {10, 7, 8, 9, 1, 5};
    int n = 6;
    printf("Original: "); print_array(arr, n);
    quick_sort(arr, 0, n-1);
    printf("Sorted:   "); print_array(arr, n);
    return 0;
}

/* Expected output:
Original: 10 7 8 9 1 5 
Sorted:   1 5 7 8 9 10 
*/