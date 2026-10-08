// Primes below 50 using trial division.
fn isPrime(n) {
    if (n < 2) { return false; }
    let d = 2;
    let prime = true;
    while (d * d <= n && prime) {
        if (n % d == 0) { prime = false; }
        d++;
    }
    return prime;
}

let count = 0;
for (let i = 2; i < 50; i++) {
    if (isPrime(i)) {
        print(i);
        count += 1;
    }
}
print("count:");
print(count);
