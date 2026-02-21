// test1_variables_ifelse.java
public class Main {
    public static void main(String[] args) {
        int age = 20;
        float gpa = 3.75f;
        char grade = 'A';

        if (age >= 18) {
            System.out.println("Adult");
        } else {
            System.out.println("Minor");
        }

        if (gpa >= 3.5f) {
            System.out.println("Dean's list");
        } else if (gpa >= 2.5f) {
            System.out.println("Good standing");
        } else {
            System.out.println("Needs improvement");
        }
    }
}
