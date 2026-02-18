import java.util.Scanner;

public class Main {

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        int n;
        System.out.println("Enter a number: ");
        n = sc.nextInt();
        int abs_val = (n >= 0 ? n : -n);
        System.out.printf("Absolute value: %d%n", abs_val);
        System.out.println("Even or odd: ");
        int is_even = (n % 2 == 0 ? 1 : 0);
        if (is_even) {
            System.out.println("Even");
        } else {
            System.out.println("Odd");
        }
        int a;
        int b;
        a = sc.nextInt();
        b = sc.nextInt();
        System.out.printf("Sum: %d%n", a + b);
        return;
    }

}