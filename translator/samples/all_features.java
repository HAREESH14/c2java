// samples/all_features.java — comprehensive test of ALL supported features
public class Main {

    // Multiple functions with different return types
    public static int max(int a, int b) {
        return a > b ? a : b;
    }

    public static float average(int a, int b) {
        return (a + b) / 2.0f;
    }

    public static void printRange(int start, int end) {
        for (int i = start; i < end; i++) {
            System.out.println(i);
        }
    }

    public static boolean isEven(int n) {
        return n % 2 == 0;
    }

    public static void main(String[] args) {
        // === Variables: all types ===
        int x = 42;
        float pi = 3.14f;
        double e = 2.718;
        char ch = 'Z';
        long big = 999999;
        short small = 10;

        // === Arithmetic + compound assignments ===
        x += 8;
        x -= 10;
        x *= 2;
        x /= 4;
        System.out.printf("x = %d%n", x);

        // === Prefix / postfix operators ===
        int a = 5;
        a++;
        ++a;
        a--;
        --a;
        System.out.printf("a = %d%n", a);

        // === if / else if / else (nested) ===
        if (x > 100) {
            System.out.println("big");
        } else if (x > 50) {
            System.out.println("medium");
        } else if (x > 10) {
            System.out.println("small");
        } else {
            System.out.println("tiny");
        }

        // === Classic for loop ===
        int sum = 0;
        for (int i = 1; i <= 10; i++) {
            sum += i;
        }
        System.out.printf("sum = %d%n", sum);

        // === While loop ===
        int count = 0;
        while (count < 5) {
            count++;
        }
        System.out.printf("count = %d%n", count);

        // === Do-while loop ===
        int n = 10;
        do {
            n -= 3;
        } while (n > 0);
        System.out.printf("n = %d%n", n);

        // === Break and continue ===
        for (int i = 0; i < 20; i++) {
            if (i % 2 == 0) continue;
            if (i > 9) break;
            System.out.println(i);
        }

        // === 1D array with new ===
        int[] arr = new int[5];
        for (int i = 0; i < 5; i++) {
            arr[i] = i * i;
        }

        // === 1D array with initializer ===
        int[] fib = {1, 1, 2, 3, 5, 8, 13};

        // === 2D array ===
        int[][] grid = new int[3][4];
        for (int i = 0; i < 3; i++) {
            for (int j = 0; j < 4; j++) {
                grid[i][j] = i * 4 + j;
            }
        }

        // === For-each loop ===
        for (int f : fib) {
            System.out.println(f);
        }

        // === Switch with multiple cases + default ===
        int day = 5;
        switch (day) {
            case 1: System.out.println("Mon"); break;
            case 2: System.out.println("Tue"); break;
            case 3: System.out.println("Wed"); break;
            case 4: System.out.println("Thu"); break;
            case 5: System.out.println("Fri"); break;
            case 6: System.out.println("Sat"); break;
            case 7: System.out.println("Sun"); break;
            default: System.out.println("Invalid"); break;
        }

        // === Function calls ===
        int biggest = max(42, 17);
        System.out.printf("max = %d%n", biggest);
        printRange(0, 3);

        // === Ternary expression ===
        int abs_val = x > 0 ? x : -x;
        System.out.printf("abs = %d%n", abs_val);

        // === println with string concatenation ===
        System.out.println("Result: " + biggest);

        // === printf with format specifiers ===
        System.out.printf("pi = %f, ch = %c%n", pi, ch);
    }
}
