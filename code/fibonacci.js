function fib(n) {
    // Base cases
    if (n === 0) return 0;
    if (n === 1) return 1;
    // Recursive rule
    return fib(n - 1) + fib(n - 2);
}

// Test examples
console.log(fib(4)); // Output: 3
console.log(fib(8)); // Output: 21
