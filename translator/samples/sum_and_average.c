// samples/sum_and_average.c — Calculate Sum and Average in C
#include <stdio.h>

float calculate_sum(int arr[], int n) {
    int i;
    float sum = 0;
    for (i = 0; i < n; i++) {
        sum = sum + arr[i];
    }
    return sum;
}

float calculate_average(int arr[], int n) {
    float sum = calculate_sum(arr, n);
    return sum / n;
}

int find_max(int arr[], int n) {
    int i;
    int max_val = arr[0];
    for (i = 1; i < n; i++) {
        if (arr[i] > max_val) {
            max_val = arr[i];
        }
    }
    return max_val;
}

int find_min(int arr[], int n) {
    int i;
    int min_val = arr[0];
    for (i = 1; i < n; i++) {
        if (arr[i] < min_val) {
            min_val = arr[i];
        }
    }
    return min_val;
}

int main() {
    int numbers[] = {45, 23, 67, 12, 89, 34, 56, 78};
    int count = 8;
    float sum, avg;
    int maximum, minimum;
    
    sum = calculate_sum(numbers, count);
    avg = calculate_average(numbers, count);
    maximum = find_max(numbers, count);
    minimum = find_min(numbers, count);
    
    printf("Sum: %.2f\n", sum);
    printf("Average: %.2f\n", avg);
    printf("Maximum: %d\n", maximum);
    printf("Minimum: %d\n", minimum);
    
    return 0;
}
