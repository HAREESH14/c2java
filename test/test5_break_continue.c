// test5_break_continue.c
// Tests break and continue inside loops

int main() {
    // break: stop at first multiple of 3
    for (int i = 1; i <= 10; i++) {
        if (i % 3 == 0) {
            printf("Breaking at: %d\n", i);
            break;
        }
        printf("%d\n", i);
    }

    // continue: skip even numbers
    int j = 0;
    while (j < 10) {
        j = j + 1;
        if (j % 2 == 0) {
            continue;
        }
        printf("Odd: %d\n", j);
    }

    // compound assignment operators
    int x = 10;
    x += 5;
    x -= 3;
    x *= 2;
    printf("x = %d\n", x);

    return 0;
}
