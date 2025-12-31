#include <stdint.h>
#include <string.h>

// Forward declarations to avoid implicit declaration errors
static uint32_t HandleException( uint32_t ir, uint32_t code );
static uint32_t HandleControlStore( uint32_t addy, uint32_t val );
static uint32_t HandleControlLoad( uint32_t addy );

extern void putchar(char c);
extern void puts(const char *s);

// RAM: 8MB
#define RAM_SIZE (8*1024*1024)
static uint8_t ram[RAM_SIZE];

// Include the compiled DTB data
#include "dtb_data.h"

// Override definitions before including the header
#define MINI_RV32_RAM_SIZE RAM_SIZE
#define MINIRV32_DECORATE  static
#define MINIRV32_IMPLEMENTATION
#define MINIRV32_POSTEXEC( pc, ir, retval ) { if(retval > 0 ) retval = HandleException( ir, retval ); }
#define MINIRV32_HANDLE_MEM_STORE_CONTROL( addy, val ) if( HandleControlStore( addy, val ) ) return val;
#define MINIRV32_HANDLE_MEM_LOAD_CONTROL( addy, rval ) rval = HandleControlLoad( addy );

#include "mini-rv32ima.h"

static uint32_t HandleException( uint32_t ir, uint32_t code ) { return code; }

static uint32_t HandleControlStore( uint32_t addy, uint32_t val )
{
    if( addy == 0x10000000 ) { putchar(val); return 0; }
    else if( addy == 0x11100000 ) { return val; } // Syscon
    return 0;
}

static uint32_t HandleControlLoad( uint32_t addy ) { return 0; }

// a0: dest_addr, a1: storage_idx (unused for now), a2: nbt_idx (unused for now)
void mc_load_data(uint32_t dest_addr) {
    asm volatile ("li a7, 13\nmv a0, %0\necall" : : "r"(dest_addr) : "a0", "a7");
}

void mc_shutdown() {
    asm volatile ("li a7, 12\nli a0, 0x5555\necall");
}

int main()
{
    puts("Starting mini-rv32ima...");
    
restart:
    mc_load_data((uint32_t)ram);
    
    struct MiniRV32IMAState core;
    memset(&core, 0, sizeof(core));
    core.pc = MINIRV32_RAM_IMAGE_OFFSET;
    core.regs[10] = 0x00; // argc
    core.regs[11] = 0x00; // argv
    core.regs[12] = MINIRV32_RAM_IMAGE_OFFSET + RAM_SIZE - sizeof(dtb_8mb); // dtb
    
    memcpy(ram + RAM_SIZE - sizeof(dtb_8mb), dtb_8mb, sizeof(dtb_8mb));
    
    puts("Booting Linux...");
    
    while(1) {
        uint32_t ret = MiniRV32IMAStep(&core, ram, 0, 500, 0);
        
        switch( ret )
        {
            case 0: break; // Continue
            case 1: // Sleep
                break;
            case 3: // Trap/Fault
                puts("\n[CORE] Processor Trap! Halted.");
                return 1;
            case 0x7777: 
                puts("\n[SYSCON] Restarting...");
                goto restart;
            case 0x5555: 
                puts("\n[SYSCON] Powering Off.");
                mc_shutdown();
                return 0;
            default:
                puts("\n[CORE] Unknown failure.");
                return 1;
        }
    }
    
    return 0;
}