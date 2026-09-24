# MiniLang Compiler

A complete compiler pipeline for **MiniLang**, a small C/JavaScript-style language, written from scratch in Python with no parser generators or external dependencies.

```
source ─▶ Lexer ─▶ Parser (AST) ─▶ Semantic Analyzer ─▶ Code Generator (TAC + pseudo-asm)
                                                      └▶ Tree-walking interpreter (runs it)
```

## Language features

- `let` / `const` declarations, `fn` functions with `return`
- `if` / `else`, `while`, `for` loops
- Arithmetic, comparison, logical and compound-assignment operators (`+=`, `++`, `&&`, …)
- Strings, integers, booleans, `null`, `print`
- `//` and `/* */` comments

## What each stage does

| Stage | Responsibility |
|---|---|
| **Lexer** | Tokenizes source with line/column tracking; builds identifier and constant tables |
| **Parser** | Recursive-descent parser producing an AST; reports syntax errors with positions |
| **Semantic analyzer** | Nested scopes and symbol table; catches use-before-declaration, redeclaration, `const` misuse and operand type errors |
| **Code generator** | Emits **three-address code** (temps, labels, conditional jumps) and a stack-style pseudo-assembly |
| **Runtime** | Tree-walking interpreter with environments and call frames that executes the program |

## Run it

Requires Python 3.9+. There are no dependencies.

```bash
python code_generator_final_product.py --demo        # built-in sample program
python code_generator_final_product.py examples/sample.ml
python code_generator_final_product.py examples/sample.ml --json   # machine-readable output
```

## Example

Input:

```js
fn add(a, b) { return a + b; }
let total = add(10, 20);
if (total > 20) { print("greater than twenty"); } else { print("small value"); }
for (let i = 0; i < 3; i++) { print(i); }
```

Generated three-address code (excerpt):

```
func add(a, b)
t1 = a + b
return t1
endfunc add
param x
param y
t2 = call add, 2
total = t2
t3 = total > 20
if_false t3 goto ELSE1
print 'greater than twenty'
goto ENDIF2
label ELSE1
...
```

## Repository layout

| File | Contents |
|---|---|
| `code_generator_final_product.py` | Full pipeline in one file (the final deliverable) |
| `final.py`, `syntax.py`, `semantic.py` | Earlier standalone stages: lexer, parser, semantic analyzer |
| `examples/` | Sample MiniLang programs |

Built for CS 453 (Compiler Design) at San Francisco Bay University.
