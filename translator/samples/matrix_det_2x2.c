// samples/matrix_det_2x2.c — determinant of 2x2 matrix
#include <stdio.h>

int main() {
    int m[2][2] = {{1,2},{3,4}};
    int det = m[0][0]*m[1][1] - m[0][1]*m[1][0];
    printf("Determinant: %d\n", det);
    return 0;
}
