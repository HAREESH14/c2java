// test3_arrays.java
public class Main {
    public static void main(String[] args) {
        int[] scores = new int[5];
        scores[0] = 90;
        scores[1] = 85;
        scores[2] = 78;
        scores[3] = 92;
        scores[4] = 88;

        for (int i = 0; i < 5; i++) {
            System.out.println(scores[i]);
        }

        int[] primes = {2, 3, 5, 7, 11};
        for (int i = 0; i < 5; i++) {
            System.out.println(primes[i]);
        }

        int[][] matrix = new int[3][3];
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3; j++) {
                matrix[i][j] = i + j;
            }
        }

        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 3; j++) {
                System.out.println(matrix[i][j]);
            }
        }
    }
}
