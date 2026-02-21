public class Main {

    public static int add(int a, int b) {
        return (a + b);
    }

    public static int factorial(int n) {
        if ((n <= 1)) {
                return 1;
        }
        return (n * factorial((n - 1)));
    }

    public static void main(String[] args) {
        int x = 5;
        int y = 3;
        int sum = add(x, y);
        System.out.printf("Sum: %d%n", sum);
        int i;
        for (i = 1; (i <= 5); i++) {
            System.out.printf("%d%n", i);
        }
        int n = 5;
        int fact = factorial(n);
        System.out.printf("Factorial of %d = %d%n", n, fact);
        if ((x > y)) {
                System.out.printf("x is greater%n");
        } else {
                System.out.printf("y is greater%n");
        }
        return;
    }

}