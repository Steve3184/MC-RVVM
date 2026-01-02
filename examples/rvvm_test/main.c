#include <stdint.h>

extern void putchar(char c);
extern void puts(const char* s);
extern void poweroff();
extern void exec_cmd(const char* cmd);

void print_test_result(const char* name, int passed) {
    puts("TEST: ");
    puts(name);
    puts(passed ? " [PASS]\n" : " [FAIL]\n");
}

int g_counter = 0;
int g_init_val = 123;

int test_alu() {
    volatile int a = 10;
    volatile int b = 20;
    volatile int c = 0;
    int failures = 0;

    c = a + b;
    if (c != 30) { puts("ADD Fail\n"); failures++; }
    
    c = b - a;
    if (c != 10) { puts("SUB Fail\n"); failures++; }
    
    c = a * b;
    if (c != 200) { puts("MUL Fail\n"); failures++; }
    
    c = 1 << 4;
    if (c != 16) { puts("SLL Fail\n"); failures++; }
    
    c = 32 >> 2;
    if (c != 8) { puts("SRL Fail\n"); failures++; }

    c = 0xF0 & 0x0F;
    if (c != 0) { puts("AND Fail\n"); failures++; }
    
    c = 0xF0 | 0x0F;
    if (c != 0xFF) { puts("OR Fail\n"); failures++; }

    return failures == 0;
}

int test_memory() {
    volatile uint32_t* ptr = (uint32_t*)&g_counter;
    *ptr = 0xDEADBEEF;
    if (g_counter != 0xDEADBEEF) return 0;
    
    if (g_init_val != 123) return 0;
    
    return 1;
}

int main() {
    puts("\n=== MC-RVVM Bare Metal Test (Transpiler) ===\n");
    
    if (test_alu()) {
        print_test_result("ALU Operations", 1);
    } else {
        print_test_result("ALU Operations", 0);
    }

    if (test_memory()) {
        print_test_result("Memory Access", 1);
    } else {
        print_test_result("Memory Access", 0);
    }

    // Test Exec Cmd
    puts("Testing exec_cmd...\n");
    exec_cmd("say \"1234567890test'\"");
    
    puts("=== All Tests Completed ===\n");
    
    poweroff();
    return 0;
}