/* Loops and branching */
let i = 0;
let total = 0;
while (i < 5) {
    total += i;
    i++;
}
print(total);

let j;
for (j = 0; j < 3; j += 1) {
    if (j == 1) {
        print("one");
    } else if (j == 2) {
        print("two");
    } else {
        print("zero");
    }
}

let flag = true;
if (flag && !false) {
    print("logic ok");
}
if (false || flag) {
    print("or ok");
}
