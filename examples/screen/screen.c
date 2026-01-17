#include "crt0.h"

uint16_t vram[SCREEN_W * SCREEN_H];

void draw_pixel(int x, int y, int color) {
    if (x >= 0 && x < SCREEN_W && y >= 0 && y < SCREEN_H) {
        vram[y * SCREEN_W + x] = color;
    }
}

void clear_screen(int color) {
    for (int i = 0; i < SCREEN_W * SCREEN_H; i++) {
        vram[i] = color;
    }
}

void draw_line(int x0, int y0, int x1, int y1, int color) {
    int dx = (x1 > x0) ? (x1 - x0) : (x0 - x1);
    int sx = (x0 < x1) ? 1 : -1;
    int dy = (y1 > y0) ? -(y1 - y0) : -(y0 - y1);
    int sy = (y0 < y1) ? 1 : -1;
    int err = dx + dy;

    while (1) {
        draw_pixel(x0, y0, color);
        if (x0 == x1 && y0 == y1) break;
        int e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; }
    }
}

void test_pattern(int color_offset) {
    for (int y = 0; y < SCREEN_H; y++) {
        for (int x = 0; x < SCREEN_W; x++) {
            int r = (x * 15) / SCREEN_W;
            int g = (y * 15) / SCREEN_H;
            int b = (color_offset % 16);
            draw_pixel(x, y, (r << 8) | (g << 4) | b);
        }
    }
    
    draw_line(0, 0, SCREEN_W-1, SCREEN_H-1, 0xFFF);
    draw_line(SCREEN_W-1, 0, 0, SCREEN_H-1, 0xFFF);
    
    int box_color = 0xF00;
    for(int i=10; i<38; i++) {
        draw_pixel(i, 10, box_color);
        draw_pixel(i, 30, box_color);
    }
    for(int i=10; i<=30; i++) {
        draw_pixel(10, i, box_color);
        draw_pixel(38, i, box_color);
    }
}

int main() {
    printf("Screen Multi-Facing Test...\n");
    int screen_id = 0;
    int x = 10, y = -55, z = 10;

    int facings[] = {
        SCREEN_FACING_NORTH,
        SCREEN_FACING_SOUTH,
        SCREEN_FACING_EAST,
        SCREEN_FACING_WEST,
        SCREEN_FACING_UP,
        SCREEN_FACING_DOWN
    };
    const char* names[] = {"NORTH", "SOUTH", "EAST", "WEST", "UP", "DOWN"};

    for (int i = 0; i < 6; i++) {
        printf("Testing Facing: %s\n", names[i]);
        screen_init(screen_id, facings[i], x, y, z);
        
        clear_screen(0x000);
        test_pattern(i * 2);
        
        screen_flush(screen_id, vram);
        printf("Flushed %s. Sleeping 60 ticks...\n", names[i]);
        sleep(60);
    }
    
    printf("Done.\n");
    halt();
    return 0;
}
