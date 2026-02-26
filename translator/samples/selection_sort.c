// samples/selection_sort.c — Selection Sort with test data
#include <stdio.h>

void selection_sort(int arr[], int n) {
    int i, j, min_idx, tmp;
    for (i = 0; i < n-1; i++) {
        min_idx = i;
        for (j = i+1; j < n; j++)
            if (arr[j] < arr[min_idx])
                min_idx = j;
        tmp = arr[min_idx];
        arr[min_idx] = arr[i];
        arr[i] = tmp;
    }
}

void print_array(int arr[], int n) {
    for (int i = 0; i < n; i++) printf("%d ", arr[i]);
    printf("\n");
}

int main() {
    int data[] = {29, 10, 14, 37, 13};
    int n = 5;
    printf("Original: "); print_array(data, n);
    selection_sort(data, n);
    printf("Sorted:   "); print_array(data, n);
    return 0;
}

/* Expected output:
Original: 29 10 14 37 13 
Sorted:   10 13 14 29 37 
*/