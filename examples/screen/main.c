#include "crt0.h"

#define SCREEN_W 48
#define SCREEN_H 40

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

int main() {
    printf("Screen Test...\n");
    printf("screen_init(10, -57, 11)\n");
    screen_init(10, -57, 11);
    
    printf("Clearing screen and flushing...\n");
    clear_screen(0x000);
    screen_flush(vram);
    
    for (int y = 0; y < SCREEN_H; y++) {
        for (int x = 0; x < SCREEN_W; x++) {
            int r = (x * 15) / SCREEN_W;
            int g = (y * 15) / SCREEN_H;
            int b = 8;
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

    printf("Drawing pattern and flushing...\n");
    screen_flush(vram);
    
    printf("Done.\n");
    halt();
    return 0;
}