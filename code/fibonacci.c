#include <stdio.h>

int fib(int n) {
    // Base cases
    if (n == 0) return 0;
    if (n == 1) return 1;
    // Recursive rule
    return fib(n - 1) + fib(n - 2);
}

int main() {
    // Test examples
    printf("%d\n", fib(4)); // Output: 3
    printf("%d\n", fib(8)); // Output: 21
    return 0;
}
