const WORDS = ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"];

/** Small counts read better as words in prose ("four hosted models"). */
export const countWord = (n: number) => WORDS[n] ?? String(n);
