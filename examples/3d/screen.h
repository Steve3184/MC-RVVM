#ifndef SCREEN_AH
#define SCREEN_AH

#define SCREEN_W 48
#define SCREEN_H 40

void screen_init();
void screen_clear(int color);
void screen_draw_pixel(int x, int y, int color);
void screen_draw_line(int x0, int y0, int x1, int y1, int color);
void screen_full_refresh();

#endif