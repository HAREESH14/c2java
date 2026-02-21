// test5_hashmap.java
import java.util.HashMap;
import java.util.Map;

public class Main {
    public static void main(String[] args) {
        HashMap<Integer, Integer> studentMap = new HashMap<>();
        studentMap.put(101, 95);
        studentMap.put(102, 87);
        studentMap.put(103, 76);

        int searchId = 102;
        if (studentMap.containsKey(searchId)) {
            int score = studentMap.get(searchId);
            System.out.printf("Score: %d%n", score);
        }
    }
}
