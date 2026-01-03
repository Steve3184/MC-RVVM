#include "screen.h"
#include "utils.h"
#include "maze_data.h"
#include "../common/crt0.h"

int G_BASE_X = 21000;
int G_BASE_Y = -56000; 
int G_BASE_Z = 1000;

#define FOV 60
#define PRECISION 1024

int cam_x, cam_y, cam_dir = 0;

void draw_background() {
    for(int y = 0; y < 20; y++) {
        for(int x = 0; x < 48; x++) screen_draw_pixel(x, y, 0x87CEEB);
    }
    for(int y = 20; y < 40; y++) {
        for(int x = 0; x < 48; x++) {
            int color = ((x/4 + y/4) % 2 == 0) ? 0x444444 : 0x555555;
            screen_draw_pixel(x, y, color);
        }
    }
}

void render_maze() {
    draw_background();

    for (int i = 0; i < 48; i++) {
        int ray_angle = (cam_dir - (FOV / 2) + (i * FOV / 48) + 360) % 360;
        
        int sin_a = get_sin(ray_angle);
        int cos_a = get_cos(ray_angle);

        int dist = 0;
        int hit = 0;
        int wall_side = 0;

        for (dist = 1; dist < 12 * PRECISION; dist += 20) {
            int rx = (cam_x + (cos_a * dist / PRECISION)) / PRECISION;
            int ry = (cam_y + (sin_a * dist / PRECISION)) / PRECISION;

            if (rx < 0 || rx >= MAP_W || ry < 0 || ry >= MAP_H) {
                hit = 0;
                break;
            }

            if (WORLD_MAP[ry * MAP_W + rx] == 1) {
                hit = 1;
                int prev_rx = (cam_x + (cos_a * (dist-20) / PRECISION)) / PRECISION;
                if (prev_rx != rx) wall_side = 1;
                break;
            }
        }

        if (hit) {
            int line_h = (PRECISION * 30) / (dist + 1); 
            if (line_h > 38) line_h = 38;

            int start_y = 20 - (line_h / 2);
            int end_y = 20 + (line_h / 2);
            
            for (int y = start_y; y < end_y; y++) {
                int color_base = wall_side ? 0xAA0000 : 0xCC0000;
                
                if ((y % 4 == 0) || (i % 8 == 0)) color_base = 0x880000;
                
                screen_draw_pixel(i, y, color_base);
            }
        }
    }
    
    screen_full_refresh();
}

int main() {
    puts("Starting 3DMaze...");
    
    screen_init();

    int path_idx = 0;
    int sub_step = 0;
    
    while (1) {
        if (path_idx >= PATH_LEN) path_idx = 0;
        int next_idx = (path_idx + 1 < PATH_LEN) ? path_idx + 1 : 0;

        int curr_x = PATH_X[path_idx] * PRECISION + (PRECISION / 2);
        int curr_y = PATH_Y[path_idx] * PRECISION + (PRECISION / 2);
        int target_x = PATH_X[next_idx] * PRECISION + (PRECISION / 2);
        int target_y = PATH_Y[next_idx] * PRECISION + (PRECISION / 2);

        cam_x = curr_x + (target_x - curr_x) * sub_step / 4;
        cam_y = curr_y + (target_y - curr_y) * sub_step / 4;

        if (target_x > curr_x) cam_dir = 0;
        else if (target_x < curr_x) cam_dir = 180;
        else if (target_y > curr_y) cam_dir = 90;
        else if (target_y < curr_y) cam_dir = 270;

        render_maze();

        sub_step++;
        if (sub_step >= 4) {
            sub_step = 0;
            path_idx++;
        }
        
    }
    return 0;
}