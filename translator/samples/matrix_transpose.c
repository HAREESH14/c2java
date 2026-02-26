// samples/matrix_transpose.c — Transpose a 3x3 matrix (no pointers)
#include <stdio.h>

void transpose(int n, int a[][3], int t[][3]) {
    for (int i=0;i<n;i++) for (int j=0;j<n;j++) t[j][i] = a[i][j];
}

void print_mat(int n, int m, int a[][3]) {
    for (int i=0;i<n;i++) { for (int j=0;j<m;j++) printf("%d ", a[i][j]); printf("\n"); }
}

int main() {
    int A[3][3] = {{1,2,3},{4,5,6},{7,8,9}};
    int T[3][3];
    printf("A:\n"); print_mat(3,3,A);
    transpose(3,A,T);
    printf("Transpose:\n"); print_mat(3,3,T);
    return 0;
}

/* Expected output:
A:
1 2 3 
4 5 6 
7 8 9 
Transpose:
1 4 7 
2 5 8 
3 6 9 
*/