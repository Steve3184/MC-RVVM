#ifndef CRT0_H
#define CRT0_H

#include <stdint.h>
#include <stddef.h>

void* memcpy(void* dest, const void* src, size_t n);
void* memset(void* s, int c, size_t n);
size_t strlen(const char* str);
char* strcpy(char* dest, const char* src);
int strcmp(const char* s1, const char* s2);
void printf(const char* fmt, ...);
char* str_append(char* dest, const char* src);
char* itoa_append(char* dest, int n);
char* fmt_coord(char* dest, int val);
void halt(void);
void poweroff(void);
void putchar(char c);
void puts(const char* str);
void print_int(int val);
void load_data(void* dest);
void exec_cmd(const char* cmd);
void _exec_cmd_256(const char* cmd);
void _exec_cmd_512(const char* cmd);
void _exec_cmd_1024(const char* cmd);
void _exec_cmd_2048(const char* cmd);
void _exec_cmd_3072(const char* cmd);
void _exec_cmd_4096(const char* cmd);
void screen_init(int screen_id, int facing, int x, int y, int z);
void screen_flush(int screen_id, void* vram);
int read_nbt(const char* source, const char* path);
void write_nbt(const char* target, const char* path, int value);
void sleep(int ticks);

#define SCREEN_FACING_NORTH 0
#define SCREEN_FACING_SOUTH 1
#define SCREEN_FACING_EAST 2
#define SCREEN_FACING_WEST 3
#define SCREEN_FACING_UP 4
#define SCREEN_FACING_DOWN 5
#define SCREEN_W 48
#define SCREEN_H 40

#endif