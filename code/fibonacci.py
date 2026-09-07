def fib(n):
    # Base cases as given: F(0)=0, F(1)=1
    if n == 0:
        return 0
    if n == 1:
        return 1
    # Recursive rule: F(n) = F(n-1) + F(n-2)
    return fib(n - 1) + fib(n - 2)


# Test your examples
print(fib(4))  # Output: 3
print(fib(8))  # Output: 21
