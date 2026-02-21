// test2_loops.java
public class Main {
    public static void main(String[] args) {
        for (int i = 1; i <= 5; i++) {
            System.out.println(i);
        }

        int sum = 0;
        int n = 1;
        while (n <= 10) {
            sum = sum + n;
            n = n + 1;
        }
        System.out.printf("Sum: %d%n", sum);

        int count = 5;
        do {
            System.out.println(count);
            count = count - 1;
        } while (count > 0);
    }
}
