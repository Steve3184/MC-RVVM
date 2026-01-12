#include "crt0.h"

int g_counter = 0;
int g_init_val = 12345;

void print_test_result(const char* name, int passed) {
    printf("TEST: %s [", name);
    if (passed) {
        printf("PASS]\n");
    } else {
        printf("FAIL]\n");
    }
}

int test_alu() {
    volatile int a = 100;
    volatile int b = 3;
    int fail = 0;

    if ((a + b) != 103) { printf("ADD Fail\n"); fail++; }
    if ((a - b) != 97)  { printf("SUB Fail\n"); fail++; }
    if ((a * b) != 300) { printf("MUL Fail\n"); fail++; }
    if ((a / b) != 33)  { printf("DIV Fail: 100/3 != 33\n"); fail++; }
    if ((a % b) != 1)   { printf("REM Fail: 100%%3 != 1\n"); fail++; }
    if ((0xF0 & 0x0F) != 0) { printf("AND Fail\n"); fail++; }
    if ((0xF0 | 0x0F) != 0xFF) { printf("OR Fail\n"); fail++; }
    if ((1 << 4) != 16) { printf("SLL Fail\n"); fail++; }

    return fail == 0;
}

int test_lib_functions() {
    char buf1[32];
    char buf2[32];
    int fail = 0;

    memset(buf1, 'A', 10);
    buf1[10] = 0;
    if (strlen(buf1) != 10) { printf("memset/strlen len fail\n"); fail++; }
    if (buf1[0] != 'A' || buf1[9] != 'A') { printf("memset content fail\n"); fail++; }

    const char* src = "HelloRV";
    memcpy(buf2, src, 8);
    if (strcmp(buf2, "HelloRV") != 0) { printf("memcpy/strcmp fail\n"); fail++; }

    strcpy(buf1, "CopyTest");
    if (strcmp(buf1, "CopyTest") != 0) { printf("strcpy fail\n"); fail++; }

    return fail == 0;
}

int test_fast_builders() {
    char buffer[64];
    char* ptr = buffer;
    int fail = 0;

    ptr = str_append(ptr, "Pos: ");
    ptr = fmt_coord(ptr, 12345);
    *ptr = 0;

    if (strcmp(buffer, "Pos: 12.345") != 0) {
        printf("fmt_coord fail. Got: '%s'\n", buffer);
        fail++;
    }

    ptr = buffer;
    ptr = itoa_append(ptr, -54321);
    *ptr = 0;
    
    if (strcmp(buffer, "-54321") != 0) {
        printf("itoa_append fail. Got: '%s'\n", buffer);
        fail++;
    }

    return fail == 0;
}

int test_ecalls() {
    int fail = 0;
    
    printf("Testing Exec Cmd (Chat Output)...\n");
    exec_cmd("say [RVVM] Hello from RISC-V!");

    printf("Testing NBT Write -> Read loop...\n");
    int magic_val = 0xCAFEBABE;
    write_nbt("rv32:temp", "magic_test", magic_val);
    int read_val = read_nbt("rv32:temp", "magic_test");
    
    if (read_val != magic_val) {
        printf("NBT RW Fail. Wrote: %d, Read: %d\n", magic_val, read_val);
        fail++;
    } else {
        printf("NBT RW Verify: OK (%x)\n", read_val);
    }
    
    exec_cmd("data remove storage rv32:temp magic_test");
    
    return fail == 0;
}

int test_sleep_ecall() {
    printf("Testing Sleep Ecall (Wait 80 ticks/4s)...\n");
    printf("Start sleep...\n");
    sleep(80);
    printf("Wake up after sleep!\n");
    return 1;
}

int main() {
    printf("\n=== MC-RVVM Standard Library Test ===\n");
    printf("Init Global Val: %d\n\n", g_init_val);

    print_test_result("ALU & Math", test_alu());
    print_test_result("Lib (Mem/Str)", test_lib_functions());
    print_test_result("Fast Builders", test_fast_builders());
    print_test_result("Ecalls (NBT/IO)", test_ecalls());
    print_test_result("Sleep Mechanism", test_sleep_ecall());

    printf("\n=== All Tests Finished ===\n");
    
    poweroff();
    return 0;
}