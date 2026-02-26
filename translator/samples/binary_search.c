// samples/binary_search.c — Binary Search Algorithm in C
#include <stdio.h>

int binary_search(int arr[], int n, int target) {
    int left = 0;
    int right = n - 1;
    int mid;
    
    while (left <= right) {
        mid = (left + right) / 2;
        
        if (arr[mid] == target) {
            return mid;
        } else if (arr[mid] < target) {
            left = mid + 1;
        } else {
            right = mid - 1;
        }
    }
    
    return -1;  // Not found
}

int main() {
    int arr[] = {5, 10, 15, 20, 25, 30, 35, 40, 45, 50};
    int n = 10;
    int target = 30;
    int result;
    
    printf("Sorted Array: ");
    int i;
    for (i = 0; i < n; i++) {
        printf("%d ", arr[i]);
    }
    printf("\n");
    
    result = binary_search(arr, n, target);
    
    if (result != -1) {
        printf("Target %d found at index %d\n", target, result);
    } else {
        printf("Target %d not found\n", target);
    }
    
    return 0;
}
