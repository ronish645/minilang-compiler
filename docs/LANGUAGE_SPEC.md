# MiniLang Language Specification (v2)

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
- **Keywords:** `let const if else while for break continue fn return print true false null`
- **Built-in functions** (reserved names): `len push pop str int`
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
| `array` | `[1, "a", [2]]` | `[1, "a", [2]]` (strings inside arrays are quoted) |

There are no objects, maps or characters: indexing a string gives a one-character string. Functions are **not** values: they can't be stored in variables or passed as arguments.

There is **no implicit conversion**. `"n=" + 5` is an error; write `"n=" + str(5)`.

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
- **A variable's type is fixed by the first value assigned to it.** The exceptions: an `int` may be stored into a `float` variable, and any variable may hold `null`. So `let n = 10; n = n / 2;` is an error, because `n / 2` is a float. Use `n = int(n / 2);`.
- A `const` array can't be reassigned, but its elements can change.

## 4. Arrays and strings

```js
let xs = [3, 1, 2];
print(xs[0]);          // 3      (indexes start at 0)
xs[1] = 10;            // assign an element
xs[2] += 5;            // compound assignment and ++ / -- work on elements
push(xs, 4);           // append to the end
let last = pop(xs);    // remove and return the last element
print(len(xs));        // 3
let grid = [[1, 2], [3, 4]];
print(grid[1][0]);     // 3

let s = "hello";
print(s[1]);           // e
print(len(s));         // 5
```

- Indexes must be ints from `0` to `len - 1`. **There are no negative indexes**: `xs[-1]` is an error, so use `xs[len(xs) - 1]`. An out-of-range index is a runtime error.
- **Arrays are references**: `let b = a;` makes `b` the same array as `a`, and a function that receives an array can modify it.
- **Strings are immutable**: `s[0] = "x"` is an error. Build a new string with `+`.
- `==` compares arrays element by element: `[1, 2] == [1, 2]` is `true`.

## 5. Built-in functions

| Function | Returns | Notes |
|---|---|---|
| `len(x)` | int | length of an array or string |
| `push(xs, v)` | null | appends `v` to array `xs` |
| `pop(xs)` | the removed element | error if `xs` is empty |
| `str(x)` | string | how `print` would show `x`: `str(42)` is `"42"`, `str(true)` is `"true"` |
| `int(x)` | int | float → int truncates toward zero (`int(7 / 2)` is `3`, `int(-7 / 2)` is `-3`); string → int parses digits (`int("42")`) |

There are no methods or properties: write `len(xs)`, not `xs.length`, and `push(xs, v)`, not `xs.push(v)`.

## 6. Operators

From lowest to highest precedence:

| Precedence | Operators | Associativity | Operand types → result |
|---|---|---|---|
| 1 | `=` `+=` `-=` `*=` `/=` | right | target is a variable or an array element |
| 2 | `\|\|` | left | bool → bool |
| 3 | `&&` | left | bool → bool |
| 4 | `==` `!=` `===` | left | any → bool |
| 5 | `<` `>` `<=` `>=` | left | numbers → bool |
| 6 | `+` `-` | left | numbers → number; `string + string` → string |
| 7 | `*` `/` `%` | left | numbers → number |
| 8 | prefix `!` `-` `++` `--` | right | `!` bool; `-` number; `++`/`--` numeric variable or element |
| 9 | postfix `++` `--`, indexing `[i]`, calls `f(x)` | left | |

Notes:
- `/` **always produces a float**: `7 / 2` is `3.5` and `4 / 2` is `2.0`. For integer division use `int(a / b)`.
- `%` is the remainder operator: `7 % 3` is `1`. Division or remainder by zero is a runtime error.
- `&&` and `||` short-circuit: the right side runs only when the left side doesn't decide the result.
- `==` compares values (`1 == 1.0` is `true`). `===` also requires the same type (`1 === 1.0` is `false`). A bool never equals a number.
- Comparisons `<` `>` `<=` `>=` work on numbers only, not strings.
- `x++` evaluates to the old value; `++x` evaluates to the new value.
- There is no `%=` operator and no ternary `? :`.

## 7. Statements

```text
print(expr);                       // prints one value followed by a newline

if (cond) { ... }
if (cond) { ... } else { ... }
if (a) { ... } else if (b) { ... } else { ... }

while (cond) { ... }

for (let i = 0; i < n; i++) { ... }   // init; condition; update
for (i = 0; i < n; i += 2) { ... }    // init may be an expression
for (;;) { ... }                      // every clause is optional

break;                                // leave the innermost loop
continue;                             // next iteration (a for loop still runs its update)

{ ... }                               // a bare block opens a scope
x = x + 1;                            // any expression followed by ;
```

Conditions must be `bool` (there is no truthiness: `if (len(xs))` is an error; write `if (len(xs) > 0)`). There is no `for ... in` / `for ... of`; loop over indexes instead.

## 8. Functions

```js
fn add(a, b) {
    return a + b;
}
print(add(2, 3));
```

- Functions in the same block can be called before their declaration, and can call each other (mutual recursion).
- Calls must pass exactly as many arguments as there are parameters.
- `return expr;` or bare `return;`. A function that ends without `return` gives `null`.
- Parameters are local variables. Functions can read and modify variables from enclosing scopes (closures).
- Functions may be declared inside other functions. `return` outside a function is an error, and `break`/`continue` can't cross a function boundary.

## 9. Type checking

Programs are checked before they run. Literal and variable types are known statically. Function parameters, call results and array elements are only known at run time, so they are accepted anywhere and checked when the program executes (gradual typing).

## 10. Errors

Every error reports a stage, a line and a column. Many errors include a `help` line, and one run reports every independent error it finds:

```
error[semantic]: variable 'totl' used before declaration
 --> prog.ml:8:7
  |
8 | print(totl);
  |       ^
  = help: did you mean 'total'?
```

| Stage | Examples |
|---|---|
| `lexer` | unexpected character, unterminated string |
| `syntax` | missing `;`, unbalanced braces, `xs.length` |
| `semantic` | undeclared variable, `const` reassignment, wrong argument count, type mismatch, `break` outside a loop |
| `runtime` | division by zero, index out of range, type mismatch involving parameters, resource limits |

## 11. Resource limits

A run is stopped with a runtime error if it executes more than 1,000,000 statements, nests more than 500 function calls, or prints more than 10,000 lines.

## 12. Differences from JavaScript and Python

| If you would write... | In MiniLang write |
|---|---|
| `function f(a) {}` / `def f(a):` | `fn f(a) { ... }` |
| `var x = 1` / `x = 1` (new variable) | `let x = 1;` |
| `xs.length`, `xs.push(v)`, `len(xs)` in Python | `len(xs)`, `push(xs, v)` |
| `"n=" + n`, `f"n={n}"` | `"n=" + str(n)` |
| `a // b`, `Math.floor(a / b)` | `int(a / b)` |
| `xs[-1]` | `xs[len(xs) - 1]` |
| `for (x of xs)`, `for x in xs:` | `for (let i = 0; i < len(xs); i++) { let x = xs[i]; ... }` |
| `cond ? a : b` | `if / else` |
| `True`, `False`, `None`, `undefined` | `true`, `false`, `null` |
| `if (xs.length)` (truthiness) | `if (len(xs) > 0)` |
| `x %= 2` | `x = x % 2;` |

## 13. Complete example

```js
// Bubble sort, then print the sorted array and its total.
fn sort(xs) {
    let n = len(xs);
    for (let i = 0; i < n; i++) {
        for (let j = 0; j < n - 1 - i; j++) {
            if (xs[j] > xs[j + 1]) {
                let tmp = xs[j];
                xs[j] = xs[j + 1];
                xs[j + 1] = tmp;
            }
        }
    }
}

let nums = [5, 3, 8, 1];
sort(nums);
print(nums);                       // [1, 3, 5, 8]

let total = 0;
for (let i = 0; i < len(nums); i++) { total += nums[i]; }
print("total: " + str(total));    // total: 17
```
