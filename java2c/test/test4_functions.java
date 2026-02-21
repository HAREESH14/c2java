// test4_functions.java
public class Main {

    public static int add(int a, int b) {
        return a + b;
    }

    public static int multiply(int a, int b) {
        return a * b;
    }

    public static int max(int a, int b) {
        if (a > b) {
            return a;
        } else {
            return b;
        }
    }

    public static void printArray(int[] arr, int size) {
        for (int i = 0; i < size; i++) {
            System.out.println(arr[i]);
        }
    }

    public static void main(String[] args) {
        int x = 5;
        int y = 3;

        int sum = add(x, y);
        int product = multiply(x, y);
        int biggest = max(x, y);

        System.out.printf("Sum: %d%n", sum);
        System.out.printf("Product: %d%n", product);
        System.out.printf("Max: %d%n", biggest);

        int[] nums = {10, 20, 30, 40, 50};
        printArray(nums, 5);
    }
}
