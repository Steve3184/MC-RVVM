#include <stdint.h>
#include <string.h>

static uint32_t HandleException( uint32_t *pc, uint32_t ir, uint32_t code );
static uint32_t HandleControlStore( uint32_t addy, uint32_t val );
static uint32_t HandleControlLoad( uint32_t addy );
extern void putchar(char c);
extern void puts(const char *s);
extern void exec_cmd(const char *cmd);

#define RAM_SIZE (10*1024*1024)
static uint8_t ram[RAM_SIZE];

struct MiniRV32IMAState *core_global = 0;

#define MINI_RV32_RAM_SIZE RAM_SIZE
#define MINIRV32_DECORATE  static

#pragma GCC push_options
#pragma GCC optimize ("Os")
#define MINIRV32_IMPLEMENTATION

#define MINIRV32_POSTEXEC( pc, ir, retval ) { if(retval > 0 ) retval = HandleException( &pc, ir, retval ); }
#define MINIRV32_HANDLE_MEM_STORE_CONTROL( addy, val ) if( HandleControlStore( addy, val ) ) return val;
#define MINIRV32_HANDLE_MEM_LOAD_CONTROL( addy, rval ) rval = HandleControlLoad( addy );

#include "mini-rv32ima.h"
#pragma GCC pop_options

#include "dtb_data.h"

static uint32_t HandleException( uint32_t *pc, uint32_t ir, uint32_t code )
{
    if (code == 9 || code == 12) {
        uint32_t a7 = core_global->regs[17];
        uint32_t a0 = core_global->regs[10];
        if (a7 == 11) {
            putchar(a0);
            *pc += 4;
            return 0;
        }
        if (a7 == 14) {
            *pc += 4;
            return 0;
        }
    }
    return code;
}

static uint32_t HandleControlStore( uint32_t addy, uint32_t val )
{
    if( addy == 0x10000000 ) { putchar(val); return 0; }
    else if( addy == 0x11004004 ) { core_global->timermatchh = val; return 0; }
    else if( addy == 0x11004000 ) { core_global->timermatchl = val; return 0; }
    else if( addy == 0x11100000 ) { core_global->pc += 4; return val; }
    return 0;
}

static uint32_t HandleControlLoad( uint32_t addy )
{
    if( addy == 0x1100bffc ) return core_global->timerh;
    if( addy == 0x1100bff8 ) return core_global->timerl;
    return 0;
}

void mc_load_data(uint32_t dest_addr) {
    asm volatile ("li a7, 13\nmv a0, %0\necall" : : "r"(dest_addr) : "a0", "a7");
}

void mc_shutdown() {
    asm volatile ("li a7, 12\nli a0, 0x5555\necall");
}

void print_hex(uint32_t val) {
    char buf[11];
    buf[0] = '0';
    buf[1] = 'x';
    for (int i = 0; i < 8; i++) {
        uint32_t nibble = (val >> (28 - i * 4)) & 0xf;
        buf[i + 2] = (nibble < 10) ? (nibble + '0') : (nibble - 10 + 'a');
    }
    buf[10] = 0;
    puts(buf);
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

    puts("Starting mini-rv32ima...\n");
    
restart:
    mc_load_data((uint32_t)ram);
    puts("Coping DTB...\n");
    
    struct MiniRV32IMAState core;
    memset(&core, 0, sizeof(core));
    core_global = &core;
    
    core.pc = MINIRV32_RAM_IMAGE_OFFSET;
    
    core.extraflags |= 3; 
    
    core.regs[10] = 0x00;
    uint32_t dtb_offset = (RAM_SIZE - sizeof(dtb_8mb) - 2048) & ~3;
    uint32_t dtb_pa = MINIRV32_RAM_IMAGE_OFFSET + dtb_offset;
    core.regs[11] = dtb_pa;
    
    memcpy(ram + dtb_offset, dtb_8mb, sizeof(dtb_8mb));
    
    exec_set_score("DTB_Offset", dtb_offset);
    exec_set_score("DTB_Size", sizeof(dtb_8mb));
    
    puts("Booting Kernel...\n");
    int cycles = 0;
    exec_set_score("KCycles", 0);
    exec_set_score("PC", core.pc);

    while(1) {
        uint32_t ret = MiniRV32IMAStep(&core, ram, 0, 500, 1024);
        
        cycles++;
        exec_set_score("KCycles", cycles);
        exec_set_score("PC", core.pc);
        
        switch( ret )
        {
            case 0: break; 
            case 1: break;
            case 3: 
                puts("\n[CORE] Processor Trap! Halted.\n");
                return 1;
            case 0x7777: 
                goto restart;
            case 0x5555: 
                puts("\n[CORE] Powering Off.\n");
                mc_shutdown();
                return 0;
            default:
                puts("\n[CORE] Unknown failure.\n");
                return 1;
        }
    }
    
    return 0;
}