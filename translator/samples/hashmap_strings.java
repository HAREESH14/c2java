// samples/hashmap_strings.java — HashMap + String operations
import java.util.HashMap;

public class Main {
    public static void main(String[] args) {
        // HashMap operations
        HashMap<Integer, Integer> scores = new HashMap<>();
        scores.put(101, 95);
        scores.put(102, 87);
        scores.put(103, 76);
        scores.put(104, 92);

        int[] ids = {101, 102, 103, 104, 105};
        for (int i = 0; i < 5; i++) {
            if (scores.containsKey(ids[i])) {
                int score = scores.get(ids[i]);
                System.out.printf("Student %d: %d%n", ids[i], score);
            } else {
                System.out.printf("Student %d: not found%n", ids[i]);
            }
        }

        // String operations
        String greeting = "Hello World";
        int len = greeting.length();
        System.out.printf("Length: %d%n", len);

        String other = "Hello World";
        if (greeting.equals(other)) {
            System.out.println("Strings are equal");
        }
    }
}
