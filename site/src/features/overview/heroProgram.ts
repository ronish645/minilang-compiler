// The hero sample. Verified with minilang.playground.explore(): it compiles
// through every stage and prints exactly HERO_OUTPUT.

export const HERO_FILENAME = "counter.ml";

export const HERO_PROGRAM = `// each closure keeps its own count
fn makeCounter(step) {
    let count = 0;
    fn next() {
        count = count + step;
        return count;
    }
    return next;
}

let byTwo = makeCounter(2);
byTwo();
byTwo();
print("count: " + str(byTwo()));
print(makeCounter(10)());
`;

export const HERO_OUTPUT = ["count: 6", "10"];
