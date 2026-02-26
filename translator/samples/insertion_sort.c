// samples/insertion_sort.c — Insertion Sort with test data
#include <stdio.h>

void insertion_sort(int arr[], int n) {
    for (int i = 1; i < n; i++) {
        int key = arr[i];
        int j = i - 1;
        while (j >= 0 && arr[j] > key) {
            arr[j+1] = arr[j];
            j = j - 1;
        }
        arr[j+1] = key;
    }
}

void print_array(int arr[], int n) {
    for (int i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\n");
}

int main() {
    int data[] = {12, 11, 13, 5, 6};
    int n = 5;
    printf("Original: "); print_array(data, n);
    insertion_sort(data, n);
    printf("Sorted:   "); print_array(data, n);
    return 0;
}

/* Expected output:
Original: 12 11 13 5 6 
Sorted:   5 6 11 12 13 
*/