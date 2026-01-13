#include <stdint.h>
#include <string.h>
#include "dtb_data.h"

static uint32_t HandleControlStore(uint32_t addy, uint32_t val);
static uint32_t HandleControlLoad(uint32_t addy);
extern void putchar(char c);
extern void puts(const char *s);
extern void exec_cmd(const char *cmd);

#define RAM_SIZE (14*1024*1024)
static uint8_t ram[RAM_SIZE];
struct MiniRV32IMAState *core;

#define MINIRV32_DECORATE  static
#define MINI_RV32_RAM_SIZE RAM_SIZE
#define MINIRV32_IMPLEMENTATION
#define MINIRV32_POSTEXEC( pc, ir, retval ) { if(retval > 0) retval = 0; }
#define MINIRV32_HANDLE_MEM_STORE_CONTROL( addy, val ) if( HandleControlStore( addy, val ) ) return val;
#define MINIRV32_HANDLE_MEM_LOAD_CONTROL( addy, rval ) rval = HandleControlLoad( addy );

#include "mini-rv32ima.h"

static uint32_t HandleControlStore(uint32_t addy, uint32_t val) {
    if (addy == 0x10000000) { putchar(val); }
    else if (addy == 0x11004004) core->timermatchh = val;
    else if (addy == 0x11004000) core->timermatchl = val;
    return 0;
}

static uint32_t HandleControlLoad(uint32_t addy) {
    if (addy == 0x10000005) return 0x60;
    if (addy == 0x1100bffc) return core->timerh;
    if (addy == 0x1100bff8) return core->timerl;
    return 0;
}


void mc_load_data(uint32_t dest_addr) {
    asm volatile ("li a7, 13\nmv a0, %0\necall" : : "r"(dest_addr) : "a0", "a7");
}

void mc_shutdown() {
    asm volatile ("li a7, 12\nli a0, 0x5555\necall");
}

void exec_set_score(const char* name, int val) {
    char buf[128];
    char* p = buf;
    const char* s = "scoreboard players set ";
    while(*s) *p++ = *s++;
    s = name;
    while(*s) *p++ = *s++;
    s = " rv_info ";
    while(*s) *p++ = *s++;
    
    if(val == 0) {
        *p++ = '0';
    } else {
        if(val < 0) {
            *p++ = '-';
            val = -val;
        }
        char num[16];
        char* n = num;
        unsigned int uval = (unsigned int)val;
        while(uval > 0) {
            *n++ = (uval % 10) + '0';
            uval /= 10;
        }
        while(n > num) *p++ = *--n;
    }
    *p = 0;
    exec_cmd(buf);
}

int main()
{
    exec_cmd("scoreboard objectives add rv_info dummy \"mini-rv32ima\"");
    exec_cmd("scoreboard objectives setdisplay sidebar rv_info");
    exec_set_score("KCycles", -1);
    exec_set_score("PC", -1);

    puts("starting mini-rv32ima...\n");
    
restart:
    mc_load_data((uint32_t)ram);
    puts("init ram...\n");
    
    uint32_t dtb_ptr = RAM_SIZE - sizeof(dtb_data) - sizeof(struct MiniRV32IMAState);
    memcpy(ram + dtb_ptr, dtb_data, sizeof(dtb_data));

    core = (struct MiniRV32IMAState *)(ram + RAM_SIZE - sizeof(struct MiniRV32IMAState));
    core->pc = MINIRV32_RAM_IMAGE_OFFSET;
    core->regs[11] = dtb_ptr + MINIRV32_RAM_IMAGE_OFFSET;
    core->extraflags |= 3;
    
    puts("booting...\n");
    int cycles = 0;
    int loop_count = 0;
    
    exec_set_score("KCycles", 0);
    exec_set_score("PC", core->pc);

    while(1) {
        uint32_t ret = MiniRV32IMAStep(core, ram, 0, 500, 1024);
        
        cycles++;
        loop_count++;

        if (loop_count % 4 == 0) {
            exec_set_score("KCycles", cycles);
            exec_set_score("PC", core->pc);
        }
        
        if (ret == 0x5555) {
            puts("stopped.\n");
            break;
        };
    }
    
    return 0;
}