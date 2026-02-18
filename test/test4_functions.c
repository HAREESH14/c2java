// test4_functions.c
int add(int a, int b) {
    return a + b;
}

int multiply(int a, int b) {
    return a * b;
}

int max(int a, int b) {
    if (a > b) {
        return a;
    } else {
        return b;
    }
}

void printArray(int arr[], int size) {
    for (int i = 0; i < size; i++) {
        printf("%d", arr[i]);
    }
}

int main() {
    int x = 5;
    int y = 3;

    int sum = add(x, y);
    int product = multiply(x, y);
    int biggest = max(x, y);

    printf("Sum: %d\n", sum);
    printf("Product: %d\n", product);
    printf("Max: %d\n", biggest);

    int nums[] = {10, 20, 30, 40, 50};
    printArray(nums, 5);

    return 0;
}
