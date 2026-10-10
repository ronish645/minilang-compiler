// MiniLang v2: arrays, strings and built-ins.
// Split a sentence into words, sort them by length, and report.
fn split(s) {
    let words = [];
    let word = "";
    for (let i = 0; i < len(s); i++) {
        if (s[i] == " ") {
            push(words, word);
            word = "";
            continue;
        }
        word = word + s[i];
    }
    push(words, word);
    return words;
}

fn sortByLength(xs) {
    for (let i = 0; i < len(xs); i++) {
        for (let j = 0; j < len(xs) - 1 - i; j++) {
            if (len(xs[j]) > len(xs[j + 1])) {
                let t = xs[j];
                xs[j] = xs[j + 1];
                xs[j + 1] = t;
            }
        }
    }
}

let words = split("compilers turn source into running programs");
sortByLength(words);
print(words);
print("longest: " + words[len(words) - 1] + " (" + str(len(words[len(words) - 1])) + " letters)");

let letters = 0;
for (let i = 0; i < len(words); i++) { letters += len(words[i]); }
print("average length: " + str(int(letters / len(words))));   // int() = integer division
