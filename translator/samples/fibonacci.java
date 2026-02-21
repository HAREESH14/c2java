// samples/fibonacci.java -- Fibonacci with multiple features
public class Main {

    public static int fib(int n) {
        if (n <= 1) return n;
        return fib(n - 1) + fib(n - 2);
    }

    public static void main(String[] args) {
        int[] results = new int[10];
        for (int i = 0; i < 10; i++) {
            results[i] = fib(i);
            System.out.printf("fib(%d) = %d%n", i, results[i]);
        }

        int x = 15;
        x += 5;
        x *= 2;
        System.out.printf("x = %d%n", x);

        int grade = 2;
        switch (grade) {
            case 1: System.out.println("A"); break;
            case 2: System.out.println("B"); break;
            case 3: System.out.println("C"); break;
            default: System.out.println("F"); break;
        }

        for (int v : results) {
            if (v > 10) break;
            System.out.println(v);
        }
    }
}
