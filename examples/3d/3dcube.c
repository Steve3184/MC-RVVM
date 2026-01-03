#include "screen.h"
#include "utils.h"
#include "../common/crt0.h"

int G_BASE_X = 21000;
int G_BASE_Y = -58000;
int G_BASE_Z = 1000;

static int vertices[8][3] = {
    {-120, -120, -120}, { 120, -120, -120}, { 120,  120, -120}, {-120,  120, -120},
    {-120, -120,  120}, { 120, -120,  120}, { 120,  120,  120}, {-120,  120,  120}
};

static int edges[12][2] = {
    {0,1}, {1,2}, {2,3}, {3,0},
    {4,5}, {5,6}, {6,7}, {7,4},
    {0,4}, {1,5}, {2,6}, {3,7}
};

static int edge_colors[12] = {
    0xFF0000, 0xFF0000, 0xFF0000, 0xFF0000,
    0x00FF00, 0x00FF00, 0x00FF00, 0x00FF00,
    0x0000FF, 0x0000FF, 0x0000FF, 0x0000FF
};

int ax = 0, ay = 0, az = 0;

void render_cube() {
    screen_clear(0x000000);

    int proj[8][2];
    
    int fov = 380;     
    int dist = 3600; 

    for (int i = 0; i < 8; i++) {
        int x = vertices[i][0];
        int y = vertices[i][1];
        int z = vertices[i][2];

        int s = get_sin(ax);
        int c = get_cos(ax);
        int y_r = (y * c - z * s) / 1024;
        int z_r = (y * s + z * c) / 1024;
        y = y_r; z = z_r;

        s = get_sin(ay); c = get_cos(ay);
        int x_r = (x * c + z * s) / 1024;
        z_r = (z * c - x * s) / 1024;
        x = x_r; z = z_r;

        s = get_sin(az); c = get_cos(az);
        x_r = (x * c - y * s) / 1024;
        y_r = (x * s + y * c) / 1024;
        x = x_r; y = y_r;

        int z_depth = dist + z;
        if (z_depth < 1) z_depth = 1;

        proj[i][0] = (x * fov) / z_depth + 24;
        proj[i][1] = (y * fov) / z_depth + 20;
    }

    for (int i = 0; i < 12; i++) {
        int p1 = edges[i][0];
        int p2 = edges[i][1];

        screen_draw_line(
            proj[p1][0], proj[p1][1],
            proj[p2][0], proj[p2][1],
            edge_colors[i]
        );
    }

    screen_full_refresh();
}

int main() {
    printf("=== 3D Cube ===\n");
    screen_init();
    
    int frame = 0;
    while (1) {
        render_cube();
        
        ax = (ax + 2) % 360;
        ay = (ay + 3) % 360;
        az = (az + 1) % 360;
        
        frame++;
        if (frame % 50 == 0) printf("Frame: %d\n", frame);
    }
    return 0;
}