#include <stdint.h>

extern void putchar(char c);
extern void puts(const char* s);

void print_num(int n) {
    if (n < 0) {
        putchar('-');
        n = -n;
    }
    if (n / 10) print_num(n / 10);
    putchar((n % 10) + '0');
}

#pragma GCC push_options
#pragma GCC optimize ("Os")

static int is_prime(int n) {
    if (n <= 1) return 0;
    if (n <= 3) return 1;
    if (n % 2 == 0 || n % 3 == 0) return 0;
    
    for (int i = 5; i * i <= n; i += 6) {
        if (n % i == 0 || n % (i + 2) == 0) return 0;
    }
    return 1;
}

int run_prime_stress_test(int limit) {
    int count = 0;
    for (int i = 2; i <= limit; i++) {
        if (is_prime(i)) {
            count++;
        }
    }
    return count;
}

#pragma GCC pop_options

int main() {
    puts("\n=== Stress Test: Prime Calc ===\n");
    
    int limit = 10000;
    puts("Calculating primes up to: ");
    print_num(limit);
    puts("\nRunning test...\n");

    int total_found = run_prime_stress_test(limit);

    puts("Test Finished.\nFound ");
    print_num(total_found);
    puts(" primes.\n");

    puts("=================================\n");
    
    return 0;
}
