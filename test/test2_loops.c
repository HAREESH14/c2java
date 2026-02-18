// test2_loops.c
int main() {
    for (int i = 1; i <= 5; i++) {
        printf("%d", i);
    }

    int sum = 0;
    int n = 1;
    while (n <= 10) {
        sum = sum + n;
        n = n + 1;
    }
    printf("Sum: %d\n", sum);

    int count = 5;
    do {
        printf("%d", count);
        count = count - 1;
    } while (count > 0);

    return 0;
}
