int sum(int a, int b) {
    int result = 0;
    for (int i = a; i < b; i++) {
        if (i % 2 == 0) {
            result += i;
        } else {
            result -= i;
        }
    }
    return result;
}
