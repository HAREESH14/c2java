#include <stdio.h>
#include <stdlib.h>

int add(int a, int b)
{
  return a + b;
}



int max(int a, int b)
{
  if (a > b)
  {
    return a;
  }
  else
  {
    return b;
  }
}



void printArray(int arr[], int size)
{
  for (int i = 0; i < size; i++)
  {
    printf("%d\n", arr[i]);
  }

}



int main()
{
  int x = 10;
  int y = 20;
  float pi = 3.14;
  int result = add(x, y);
  printf("Sum: %d\n", result);
  if (x < y)
  {
    printf("x is smaller\n");
  }
  else
    if (x == y)
  {
    printf("equal\n");
  }
  else
  {
    printf("y is smaller\n");
  }
  for (int i = 0; i < 5; i++)
  {
    printf("%d\n", i);
  }

  int n = 1;
  while (n <= 3)
  {
    printf("%d\n", n);
    n = n + 1;
  }

  int count = 3;
  do
  {
    printf("%d\n", count);
    count = count - 1;
  }
  while (count > 0);
  int scores[5];
  scores[0] = 90;
  scores[1] = 85;
  scores[2] = 78;
  scores[3] = 92;
  scores[4] = 88;
  int primes[] = {2, 3, 5, 7, 11};
  for (int i = 0; i < 5; i++)
  {
    printf("%d\n", primes[i]);
  }

  int matrix[3][3];
  for (int i = 0; i < 3; i++)
  {
    for (int j = 0; j < 3; j++)
    {
      matrix[i][j] = i + j;
    }

  }

  printArray(scores, 5);
  return 0;
}


