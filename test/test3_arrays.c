// test3_arrays.c
int main() {
    int scores[5];
    scores[0] = 90;
    scores[1] = 85;
    scores[2] = 78;
    scores[3] = 92;
    scores[4] = 88;

    for (int i = 0; i < 5; i++) {
        printf("%d", scores[i]);
    }

    int primes[] = {2, 3, 5, 7, 11};
    for (int i = 0; i < 5; i++) {
        printf("%d", primes[i]);
    }

    int matrix[3][3];
    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            matrix[i][j] = i + j;
        }
    }

    for (int i = 0; i < 3; i++) {
        for (int j = 0; j < 3; j++) {
            printf("%d", matrix[i][j]);
        }
    }

    return 0;
}
