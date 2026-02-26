// samples/matrix_multiply.c — Multiply 2x2 matrices with test data
#include <stdio.h>

void multiply_2x2(int A[2][2], int B[2][2], int C[2][2]) {
    for (int i = 0; i < 2; ++i)
        for (int j = 0; j < 2; ++j) {
            C[i][j] = 0;
            for (int k = 0; k < 2; ++k)
                C[i][j] += A[i][k] * B[k][j];
        }
}

void print_mat(int M[2][2]) {
    for (int i = 0; i < 2; ++i) {
        for (int j = 0; j < 2; ++j) printf("%d ", M[i][j]);
        printf("\n");
    }
}

int main() {
    int A[2][2] = {{1,2},{3,4}};
    int B[2][2] = {{5,6},{7,8}};
    int C[2][2];
    printf("Matrix A:\n"); print_mat(A);
    printf("Matrix B:\n"); print_mat(B);
    multiply_2x2(A,B,C);
    printf("A x B =\n"); print_mat(C);
    return 0;
}

/* Expected output:
Matrix A:
1 2 
3 4 
Matrix B:
5 6 
7 8 
A x B =
19 22 
43 50 
*/