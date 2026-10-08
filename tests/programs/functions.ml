// Recursion, nested calls, shadowing
fn fact(n) {
    if (n <= 1) {
        return 1;
    }
    return n * fact(n - 1);
}
print(fact(5));

fn fib(n) {
    if (n < 2) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}
print(fib(10));

fn square(x) { return x * x; }
fn sumSquares(a, b) { return square(a) + square(b); }
print(sumSquares(3, 4));

let x = 1;
{
    let x = 2;
    print(x);
}
print(x);
