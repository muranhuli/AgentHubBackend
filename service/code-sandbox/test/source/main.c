#include <stdio.h>

int main() {
    int a, b;
    if (scanf("%d %d", &a, &b) != 2) return 1;
    printf("%d\n", a + b);
    return 0;
}
