// Plain-English readings of the most common compiler errors. Each one links an
// error pattern (as normalised by bench/export.py) to the habit that usually
// produces it, based on docs/LANGUAGE_SPEC.md's "habits from other languages".

export interface ErrorHabit {
  habit: string;
  example?: string;
  fix?: string;
}

export const ERROR_HABITS: Record<string, ErrorHabit> = {
  "expected ';' but found '.'": {
    habit: "Method and property calls carried over from JavaScript and Python. MiniLang has no methods.",
    example: "xs.length",
    fix: "len(xs)",
  },
  "expected '(' but found '…'": {
    habit: "Control flow without parentheses, Python style. MiniLang needs C-style loops and conditions.",
    example: "for x in xs:",
    fix: "for (let i = 0; i < len(xs); i++) { … }",
  },
  "expected ';' but found '…'": {
    habit: "A statement MiniLang doesn't parse, often a missing semicolon or syntax from another language.",
    example: "let x = 1",
    fix: "let x = 1;",
  },
  "variable '…' assigned before declaration": {
    habit: "Creating a variable by assigning to it, as Python does. MiniLang declares variables with let.",
    example: "total = 0;",
    fix: "let total = 0;",
  },
  "unexpected character '?'": {
    habit: "The JavaScript ternary operator, which MiniLang doesn't have.",
    example: "x > 0 ? a : b",
    fix: "an if / else",
  },
  "'…' is not a declared function": {
    habit: "Calling a function MiniLang doesn't provide, usually one borrowed from another language's library.",
  },
  "expected ';' but found ','": {
    habit: "Comma-separated declarations or tuple-style assignment, which MiniLang doesn't support.",
    example: "let a = 1, b = 2;",
    fix: "let a = 1; let b = 2;",
  },
  "expected ')' but found ','": {
    habit: "A call or condition with an argument list MiniLang doesn't accept, such as an extra argument.",
  },
  "cannot assign float to '…' of type int": {
    habit: "The float-division trap: / always returns a float, and a variable's type is fixed.",
    example: "n = n / 2;",
    fix: "n = int(n / 2);",
  },
  "'…' is a built-in function and cannot be redefined": {
    habit: "Defining a helper with a reserved built-in name such as len or max.",
  },
};
