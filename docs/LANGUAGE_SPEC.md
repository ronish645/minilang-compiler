# MiniLang Language Specification

MiniLang is a small, dynamically executed, statically checked language with C/JavaScript-style syntax. A program is a sequence of statements run top to bottom. There is no `main` function.

```js
fn fact(n) {
    if (n <= 1) { return 1; }
    return n * fact(n - 1);
}
print(fact(5));   // 120
```

## 1. Lexical structure

- **Comments:** `// to end of line` and `/* block */`. Block comments do not nest.
- **Identifiers:** a letter or `_` followed by letters, digits or `_`. Case-sensitive.
- **Keywords:** `let const if else while for fn return print true false null`
- **Integers:** `0`, `42`. There is no leading `-` in a literal; `-5` is unary minus applied to `5`. Integers have arbitrary precision.
- **Floats:** `3.14`, `1e5`, `2.5E-3`. A digit is required after `.`.
- **Strings:** `"double"` or `'single'` quoted. Escapes: `\n \t \\ \' \"`. Inside single quotes, `''` is a literal `'`.
- Every statement ends with `;`, except blocks and `if`/`while`/`for`/`fn`, which end with `}`.

## 2. Types and values

| Type | Examples | Printed as |
|---|---|---|
| `int` | `0`, `-7`, `123456789012` | `-7` |
| `float` | `3.5`, `1e3`, `7 / 2` | `3.5`, `1000.0`, `2.0` |
| `string` | `"hi"` | `hi` (no quotes) |
| `bool` | `true`, `false` | `true` |
| `null` | `null` | `null` |

There are **no** arrays, objects, characters or string indexing, and no built-in functions besides `print`. Functions are **not** values: they cannot be stored in variables or passed as arguments.

There is **no implicit conversion**. `"n=" + 5` is an error, so print text and numbers with separate `print` calls.

## 3. Variables and scope

```js
let x = 10;        // mutable
let y;             // declared without a value: holds null
const LIMIT = 3;   // must be initialized; can never be reassigned
x = 20;
```

- A variable must be declared before it is used.
- Declaring the same name twice **in the same scope** is an error. An inner block may shadow an outer name.
- Every `{ ... }` block opens a new scope. A `for` loop's `let` variable is visible only inside the loop.
- A variable's type is fixed by the first value assigned to it, except that an `int` may be stored into a `float` variable and any variable may hold `null`.

## 4. Operators

From lowest to highest precedence:

| Precedence | Operators | Associativity | Operand types → result |
|---|---|---|---|
| 1 | `=` `+=` `-=` `*=` `/=` | right | target must be a variable |
| 2 | `\|\|` | left | bool → bool |
| 3 | `&&` | left | bool → bool |
| 4 | `==` `!=` `===` | left | any → bool |
| 5 | `<` `>` `<=` `>=` | left | numbers → bool |
| 6 | `+` `-` | left | numbers → number; `string + string` → string |
| 7 | `*` `/` `%` | left | numbers → number |
| 8 | prefix `!` `-` `++` `--` | right | `!` bool; `-` number; `++`/`--` number variable |
| 9 | postfix `++` `--` | left | number variable |

Notes:
- `/` **always produces a float**: `7 / 2` is `3.5` and `4 / 2` is `2.0`. To get integer results, avoid `/` or use `%` (for example `(n - n % 10) / 10` is still a float).
- `%` is the remainder operator: `7 % 3` is `1`.
- Division or remainder by zero is a runtime error.
- `&&` and `||` **evaluate both operands** (no short-circuiting).
- `==` compares values (`1 == 1.0` is `true`). `===` also requires the same type (`1 === 1.0` is `false`). A bool never equals a number.
- `x++` evaluates to the old value; `++x` evaluates to the new value.
- There is no `%=` operator.

## 5. Statements

```text
print(expr);                       // prints one value followed by a newline

if (cond) { ... }
if (cond) { ... } else { ... }
if (a) { ... } else if (b) { ... } else { ... }

while (cond) { ... }

for (let i = 0; i < n; i++) { ... }   // init; condition; update
for (i = 0; i < n; i += 2) { ... }    // init may be an expression
for (;;) { ... }                      // every clause is optional

{ ... }                               // a bare block opens a scope
x = x + 1;                            // any expression followed by ;
```

Conditions must be `bool`. MiniLang has **no `break` or `continue`**. To leave a loop early, make the condition false or `return` from the enclosing function.

## 6. Functions

```js
fn add(a, b) {
    return a + b;
}
print(add(2, 3));
```

- A function must be declared **before** the code that calls it. A function may call itself (recursion).
- Calls must pass exactly as many arguments as there are parameters.
- `return expr;` or bare `return;`. A function that ends without `return` gives `null`.
- Parameters are local variables. Functions can read and modify variables from enclosing scopes (closures).
- Functions may be declared inside other functions.
- `return` outside a function is an error.

## 7. Type checking

Programs are checked before they run. Literal and variable types are known statically. Function parameters and call results are only known at run time, so they are accepted anywhere and checked when the program executes (gradual typing).

## 8. Errors

Every error reports a stage, a line and a column:

```
error[semantic]: variable 'y' used before declaration
 --> prog.ml:2:7
  |
2 | print(y);
  |       ^
```

| Stage | Examples |
|---|---|
| `lexer` | unexpected character, unterminated string |
| `syntax` | missing `;`, unbalanced braces |
| `semantic` | undeclared variable, `const` reassignment, wrong argument count, type mismatch |
| `runtime` | division by zero, type mismatch involving parameters, resource limits |

## 9. Resource limits

A run is stopped with a runtime error if it executes more than 1,000,000 statements, nests more than 500 function calls, or prints more than 10,000 lines.

## 10. Complete example

```js
// Print the primes below 30, then how many there were.
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
for (let i = 2; i < 30; i++) {
    if (isPrime(i)) {
        print(i);
        count += 1;
    }
}
print("count:");
print(count);
```
