// test1_variables_ifelse.c
int main() {
    int age = 20;
    float gpa = 3.75;
    char grade = 'A';

    if (age >= 18) {
        printf("Adult\n");
    } else {
        printf("Minor\n");
    }

    if (gpa >= 3.5) {
        printf("Dean's list\n");
    } else if (gpa >= 2.5) {
        printf("Good standing\n");
    } else {
        printf("Needs improvement\n");
    }

    return 0;
}
