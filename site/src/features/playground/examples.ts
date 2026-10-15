// Example programs. Every one was run through minilang.playground.explore()
// and its output (or its failing stage) checked before shipping.

export type ExampleGroup = "Programs" | "Errors & hints";

export interface Example {
  id: string;
  title: string;
  group: ExampleGroup;
  blurb: string;
  source: string;
}

export const EXAMPLES: Example[] = [
  {
    id: "tour",
    title: "A quick tour",
    group: "Programs",
    blurb: "Recursion, closures, arrays and strings in one program.",
    source: `// A quick tour: recursion, closures, arrays and strings.
fn fib(n) {
    if (n < 2) { return n; }
    return fib(n - 1) + fib(n - 2);
}

let fibs = [];
for (let i = 0; i < 10; i++) {
    push(fibs, fib(i));
}
print(fibs);

fn makeAdder(n) {
    fn add(x) { return x + n; }
    return add;
}
let addFive = makeAdder(5);
print("makeAdder(5)(10) = " + str(addFive(10)));

let word = "compiler";
let shout = "";
for (let i = 0; i < len(word); i++) {
    shout = shout + chr(ord(word[i]) - 32);
}
print(shout + "!");
`,
  },
  {
    id: "fibonacci",
    title: "Hello + Fibonacci",
    group: "Programs",
    blurb: "A loop, string building with str().",
    source: `// Hello, world, then the first 15 Fibonacci numbers.
print("Hello, MiniLang!");

let a = 0;
let b = 1;
for (let i = 0; i < 15; i++) {
    print("fib(" + str(i) + ") = " + str(a));
    let next = a + b;
    a = b;
    b = next;
}
`,
  },
  {
    id: "binary-search",
    title: "Binary search",
    group: "Programs",
    blurb: "while, else-if chains and int(a / b).",
    source: `// Binary search over a sorted array. Returns the index, or -1.
fn search(xs, target) {
    let lo = 0;
    let hi = len(xs) - 1;
    while (lo <= hi) {
        let mid = int((lo + hi) / 2);
        if (xs[mid] == target) {
            return mid;
        } else if (xs[mid] < target) {
            lo = mid + 1;
        } else {
            hi = mid - 1;
        }
    }
    return -1;
}

let primes = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29];
let queries = [2, 13, 29, 4];
for (let i = 0; i < len(queries); i++) {
    let q = queries[i];
    print("search(" + str(q) + ") -> " + str(search(primes, q)));
}
`,
  },
  {
    id: "closures",
    title: "Closures",
    group: "Programs",
    blurb: "makeAdder(5)(10), a counter, functions in arrays.",
    source: `// Functions are values: return them, store them, pass them around.
fn makeAdder(n) {
    fn add(x) { return x + n; }
    return add;
}
print(makeAdder(5)(10));            // 15

fn makeCounter() {
    let count = 0;
    fn next() {
        count++;
        return count;
    }
    return next;
}
let tick = makeCounter();
tick();
tick();
print("counter: " + str(tick()));   // 3

fn twice(f, x) { return f(f(x)); }
print(twice(makeAdder(3), 1));      // 7

let ops = [makeAdder(1), makeAdder(100)];
for (let i = 0; i < len(ops); i++) {
    print(ops[i](41));
}
`,
  },
  {
    id: "bubble-sort",
    title: "Bubble sort",
    group: "Programs",
    blurb: "Arrays are references; break out early.",
    source: `// Bubble sort. Arrays are references, so sort() changes the caller's array.
fn sort(xs) {
    let n = len(xs);
    for (let i = 0; i < n; i++) {
        let swapped = false;
        for (let j = 0; j < n - 1 - i; j++) {
            if (xs[j] > xs[j + 1]) {
                let tmp = xs[j];
                xs[j] = xs[j + 1];
                xs[j + 1] = tmp;
                swapped = true;
            }
        }
        if (!swapped) { break; }
    }
}

let nums = [29, 4, 17, 8, 42, 1, 15];
print("before: " + str(nums));
sort(nums);
print("after:  " + str(nums));

let total = 0;
for (let i = 0; i < len(nums); i++) { total += nums[i]; }
print("sum " + str(total) + ", mean " + str(total / len(nums)));
`,
  },
  {
    id: "caesar",
    title: "Caesar cipher",
    group: "Programs",
    blurb: "ord/chr arithmetic and slice() on strings.",
    source: `// Caesar cipher with ord/chr, plus slice() on strings.
fn shift(c, k) {
    let code = ord(c);
    if (code >= ord("a") && code <= ord("z")) {
        return chr((code - ord("a") + k) % 26 + ord("a"));
    }
    return c;
}

fn encode(text, k) {
    let out = "";
    for (let i = 0; i < len(text); i++) {
        out = out + shift(text[i], k);
    }
    return out;
}

let secret = encode("hello compiler", 3);
print(secret);                       // khoor frpslohu
print(encode(secret, 23));           // back to the original
print(slice(secret, 0, 5));          // first word only
`,
  },
  {
    id: "type-joins",
    title: "If/else type joins",
    group: "Programs",
    blurb: "How the gradual type checker handles branches.",
    source: `// A variable declared without a value takes the type of its first
// assignment. When if/else branches disagree, the checker defers to run time.
let score = 87;
let grade;
if (score >= 90) {
    grade = "A";
} else {
    grade = "B";
}
print("grade: " + grade);           // both branches are strings

let result;
if (score > 50) {
    result = score / 10;            // float
} else {
    result = "low";                 // string
}
print(result);                      // type known only at run time

let half = 7 / 2;                   // '/' always gives a float
print(half);
print(int(half));                   // truncate back to an int
`,
  },
  {
    id: "js-habits",
    title: "JS & Python habits",
    group: "Errors & hints",
    blurb: "var, xs.length and xs.push(): three syntax hints.",
    source: `// Habits carried over from JavaScript and Python.
// Run it and read the fix-it hints, then fix the code.
var total = 0;
let xs = [1, 2, 3];
for (let i = 0; i < xs.length; i++) {
    total += xs[i];
}
xs.push(4);
print("total: " + str(total));
`,
  },
  {
    id: "type-errors",
    title: "Type errors",
    group: "Errors & hints",
    blurb: 'True, "n=" + n, a typo and a const write.',
    source: `// These parse fine but fail the type checker, which reports
// every independent error in one pass.
let total = 0;
let done = True;
let xs = [4, 8, 15];
for (let i = 0; i < len(xs); i++) {
    total += xs[i];
}
print("total: " + total);
print(totl);
const LIMIT = 3;
LIMIT = 4;
`,
  },
  {
    id: "division-by-zero",
    title: "Division by zero",
    group: "Errors & hints",
    blurb: "A runtime error after some output.",
    source: `// Prints a few lines, then divides by zero.
// Output produced before the error is kept.
fn average(xs) {
    let sum = 0;
    for (let i = 0; i < len(xs); i++) { sum += xs[i]; }
    return sum / len(xs);
}

print(average([2, 4, 6]));
print(average([10]));
print(average([]));
print("never printed");
`,
  },
  {
    id: "infinite-loop",
    title: "Infinite loop",
    group: "Errors & hints",
    blurb: "Stopped by the compiler's step limit.",
    source: `// An infinite loop. The step limit stops it instead of freezing the page.
let n = 0;
while (true) {
    n++;
}
print(n);
`,
  },
];

export const DEFAULT_EXAMPLE = EXAMPLES[0];

export const EXAMPLE_GROUPS: ExampleGroup[] = ["Programs", "Errors & hints"];

export const findExample = (id: string) => EXAMPLES.find((e) => e.id === id);
