#include "screen.h"
#include "utils.h"
#include "../common/crt0.h"

extern void exec_cmd(const char* cmd);

extern int G_BASE_X;
extern int G_BASE_Y;
extern int G_BASE_Z;

static char cmd_templates[40][3500];
static char* color_ptrs[40][48];
static int framebuffer[SCREEN_W * SCREEN_H];
static int last_framebuffer[SCREEN_W * SCREEN_H];

static void init_templates() {
    printf("[Screen] Init templates...\n");

    char master_json[4096];
    char* p = master_json;
    
    p = str_append(p, "[");
    for (int i = 0; i < 48; i++) {
        if (i > 0) *p++ = ',';
        
        p = str_append(p, "{\\\"text\\\":");
        
        if (i == 23) p = str_append(p, "\\\".\\\\n\\\"");
        else p = str_append(p, "\\\".\\\"");
        
        p = str_append(p, ",\\\"color\\\":\\\"#");
        p = str_append(p, "000000\\\"}");
    }
    p = str_append(p, "]");
    *p = '\0';

    int offsets[48];
    int offset_cnt = 0;
    char* scan = master_json;
    while (*scan && offset_cnt < 48) {
        if (*scan == '#' && scan[7] == '\\') {
            offsets[offset_cnt++] = (int)(scan - master_json) + 1;
        }
        scan++;
    }
    printf("[Screen] Offsets: %d\n", offset_cnt);

    for (int id = 1; id <= 40; id++) {
        int idx = id - 1;
        char* t = cmd_templates[idx];
        
        t = str_append(t, "data modify entity @e[type=text_display,tag=3d_t");
        t = itoa_append(t, id);
        t = str_append(t, ",limit=1] text set value \"");
        
        char* json_start = t;
        strcpy(t, master_json);
        
        for (int i = 0; i < 48; i++) {
            color_ptrs[idx][i] = json_start + offsets[i];
        }
        
        t += strlen(master_json);
        *t++ = '\"'; 
        *t = '\0';
    }
    printf("[Screen] Templates done.\n");
}

void screen_init() {
    char cmd[512];
    int id = 1;

    printf("[Screen] Summoning...\n");
    exec_cmd("kill @e[type=text_display,tag=3d_engine]");

    for (int block = 0; block < 2; block++) {
        int by = (block == 0) ? 0 : -500;
        
        for (int row = 0; row < 5; row++) {
            int ry = -(row * 50);
            
            for (int layer = 0; layer < 4; layer++) {
                int ox = (layer % 2 != 0) ? 25 : 0;
                int oy = (layer >= 2) ? -25 : 0;
                
                char* p = cmd;
                p = str_append(p, "summon text_display ");
                p = fmt_coord(p, G_BASE_X + ox); *p++ = ' ';
                p = fmt_coord(p, G_BASE_Y + by + ry + oy); *p++ = ' ';
                p = fmt_coord(p, G_BASE_Z);
                
                p = str_append(p, " {Tags:[\"3d_engine\",\"3d_t");
                p = itoa_append(p, id);
                p = str_append(p, "\"],billboard:\"fixed\",alignment:\"left\",background:0}");
                
                exec_cmd(cmd);
                id++;
            }
        }
    }

    init_templates();
    
    for (int i = 0; i < SCREEN_W * SCREEN_H; i++) {
        last_framebuffer[i] = 0; 
        framebuffer[i] = 0;
    }
    
    printf("[Screen] Ready.\n");
}

void screen_clear(int color) {
    for (int i = 0; i < SCREEN_W * SCREEN_H; i++) framebuffer[i] = color;
}

void screen_draw_pixel(int x, int y, int color) {
    if (x >= 0 && x < SCREEN_W && y >= 0 && y < SCREEN_H) {
        framebuffer[y * SCREEN_W + x] = color;
    }
}

void screen_draw_line(int x0, int y0, int x1, int y1, int color) {
    int dx = (x1 > x0) ? (x1 - x0) : (x0 - x1);
    int sx = (x0 < x1) ? 1 : -1;
    int dy = (y1 > y0) ? -(y1 - y0) : -(y0 - y1);
    int sy = (y0 < y1) ? 1 : -1;
    int err = dx + dy;

    while (1) {
        screen_draw_pixel(x0, y0, color);
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; }
    }
}

void screen_full_refresh() {
    for (int id = 1; id <= 40; id++) {
        int idx = id - 1;
        
        int block = idx / 20;
        int rem = idx % 20;
        int row = rem / 4;
        int layer = rem % 4;
        
        int base_y = (block * 20) + (row * 2);
        
        int is_dirty = 0;
        
        for (int i = 0; i < 48; i++) {
            int is_row2 = (i >= 24);
            int char_idx = is_row2 ? (i - 24) : i;
            
            int lx = (char_idx * 2) + (layer % 2);
            int ly = base_y;
            if (is_row2) ly += 10;
            if (layer >= 2) ly += 1;
            
            if (lx >= SCREEN_W || ly >= SCREEN_H) continue;
            
            int p_idx = ly * SCREEN_W + lx;
            int color = framebuffer[p_idx];
            
            if (color != last_framebuffer[p_idx]) {
                is_dirty = 1;
                write_hex_fast(color_ptrs[idx][i], color);
                last_framebuffer[p_idx] = color;
            }
        }
        
        if (is_dirty) exec_cmd(cmd_templates[idx]);
    }
}