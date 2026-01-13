#include "crt0.h"

#define WIDTH 48
#define HEIGHT 40

uint16_t vram[WIDTH * HEIGHT];

#define ABS(x) ((x) < 0 ? -(x) : (x))
#define PI 3.14159f

#define SHIFT 8
#define SCALE (1 << SHIFT) 

const int sin_table[64] = {
    0, 6, 13, 20, 26, 33, 40, 46, 53, 59, 66, 72, 79, 85, 91, 97, 103, 109, 115, 121, 126, 132, 137, 142, 147, 152, 157, 162, 167, 171, 176, 180, 184, 188, 192, 196, 200, 203, 207, 210, 213, 216, 219, 222, 225, 227, 230, 232, 234, 236, 238, 240, 242, 243, 245, 246, 247, 248, 250, 250, 251, 252, 252, 253
};

int get_sin(int angle) {
    angle %= 360;
    if (angle < 0) angle += 360;
    
    int sign = 1;
    if (angle >= 180) {
        angle -= 180;
        sign = -1;
    }
    
    if (angle > 90) angle = 180 - angle;
    
    int idx = (angle * 63) / 90;
    return sin_table[idx] * sign;
}

int get_cos(int angle) {
    return get_sin(angle + 90);
}

void draw_pixel(int x, int y, int color) {
    if (x >= 0 && x < WIDTH && y >= 0 && y < HEIGHT) {
        vram[y * WIDTH + x] = (uint16_t)color;
    }
}

void draw_line(int x0, int y0, int x1, int y1, int color) {
    int dx = ABS(x1 - x0), sx = x0 < x1 ? 1 : -1;
    int dy = -ABS(y1 - y0), sy = y0 < y1 ? 1 : -1;
    int err = dx + dy, e2;

    while (1) {
        draw_pixel(x0, y0, color);
        if (x0 == x1 && y0 == y1) break;
        e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; }
    }
}

typedef struct {
    int x, y, z;
} Point3D;

typedef struct {
    int x, y;
} Point2D;

int main() {
    printf("Initializing...\n");
    screen_init(10, -57, 11);

    const int S = 40; 
    Point3D cube[8] = {
        {-S, -S, -S}, {S, -S, -S}, {S, S, -S}, {-S, S, -S},
        {-S, -S, S},  {S, -S, S},  {S, S, S},  {-S, S, S}
    };

    const int edges[12][2] = {
        {0,1}, {1,2}, {2,3}, {3,0},
        {4,5}, {5,6}, {6,7}, {7,4},
        {0,4}, {1,5}, {2,6}, {3,7}
    };

    const int colors[12] = {
        0xF00, 0x0F0, 0x00F, 0xFF0,
        0x0FF, 0xF0F, 0xFFF, 0xF80,
        0x8F0, 0x08F, 0x80F, 0xAAA
    };

    int angleX = 0, angleY = 0, angleZ = 0;
    
    int frames = 0;

    printf("Starting Render Loop...\n");

    while (1) {
        for (int i = 0; i < WIDTH * HEIGHT; i++) {
            vram[i] = 0x000;
        }

        int sx = get_sin(angleX), cx = get_cos(angleX);
        int sy = get_sin(angleY), cy = get_cos(angleY);
        int sz = get_sin(angleZ), cz = get_cos(angleZ);

        Point2D projected[8];

        for (int i = 0; i < 8; i++) {
            int x = cube[i].x;
            int y = cube[i].y;
            int z = cube[i].z;

            int y1 = (y * cx - z * sx) >> SHIFT;
            int z1 = (y * sx + z * cx) >> SHIFT;
            
            int x2 = (x * cy - z1 * sy) >> SHIFT;
            int z2 = (x * sy + z1 * cy) >> SHIFT;

            int x3 = (x2 * cz - y1 * sz) >> SHIFT;
            int y3 = (x2 * sz + y1 * cz) >> SHIFT;

            int dist = 120;
            int z_factor = dist + z2; 
            if (z_factor <= 0) z_factor = 1;

            projected[i].x = (x3 * 24) / z_factor + (WIDTH / 2);
            projected[i].y = (y3 * 24) / z_factor + (HEIGHT / 2);
        }

        for (int i = 0; i < 12; i++) {
            int p1 = edges[i][0];
            int p2 = edges[i][1];
            draw_line(projected[p1].x, projected[p1].y, 
                      projected[p2].x, projected[p2].y, 
                      colors[i]);
        }

        screen_flush(vram);

        angleX = (angleX + 2) % 360;
        angleY = (angleY + 3) % 360;
        angleZ = (angleZ + 1) % 360;
        
        frames++;
        if (frames % 100 == 0) {
            printf("Frames: %d\n", frames);
        }
    }

    return 0;
}