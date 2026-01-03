#include "screen.h"
#include "utils.h"
#include "../common/crt0.h"

int G_BASE_X = 21000;
int G_BASE_Y = -56000; 
int G_BASE_Z = 1000;

#define PRECISION 1024
#define PRECISION_SHIFT 10
#define MAX_DEPTH 2
#define BIG_DIST 999999999

typedef struct {
    int x, y, z;
} Vec3;

int isqrt(int n) {
    if (n <= 0) return 0;
    int res = 0;
    int bit = 1 << 30;
    
    while (bit > n) bit >>= 2;
    
    while (bit != 0) {
        if (n >= res + bit) {
            n -= res + bit;
            res = (res >> 1) + bit;
        } else {
            res >>= 1;
        }
        bit >>= 2;
    }
    return res;
}

Vec3 v_add(Vec3 a, Vec3 b) { return (Vec3){a.x + b.x, a.y + b.y, a.z + b.z}; }
Vec3 v_sub(Vec3 a, Vec3 b) { return (Vec3){a.x - b.x, a.y - b.y, a.z - b.z}; }

Vec3 v_mul(Vec3 a, int s) { 
    return (Vec3){
        (a.x * s) >> PRECISION_SHIFT, 
        (a.y * s) >> PRECISION_SHIFT, 
        (a.z * s) >> PRECISION_SHIFT
    }; 
}

int v_dot(Vec3 a, Vec3 b) {
    long long res = (long long)a.x * b.x + (long long)a.y * b.y + (long long)a.z * b.z;
    return (int)(res >> PRECISION_SHIFT); 
}

int v_len(Vec3 a) {
    return isqrt(sq * PRECISION);
}

Vec3 v_norm(Vec3 a) {
    int l = v_len(a);
    if (l == 0) return (Vec3){0,0,0};
    
    return (Vec3){
        (a.x * PRECISION) / l,
        (a.y * PRECISION) / l,
        (a.z * PRECISION) / l
    };
}

typedef struct {
    Vec3 pos;
    int r;
    int color;
    int reflect;
} Sphere;

Sphere spheres[2];
Vec3 light_pos;

typedef struct {
    int t;
    Vec3 p;
    Vec3 n;
    int mat_col;
    int reflect;
    int hit;
} HitRec;

void intersect_sphere(Vec3 ro, Vec3 rd, Sphere s, HitRec* rec) {
    Vec3 oc = v_sub(ro, s.pos);
    int b = v_dot(oc, rd);
    int c = v_dot(oc, oc) - (s.r * s.r) / PRECISION * PRECISION;
    int h = (int)(((long long)b * b >> PRECISION_SHIFT) - c);
    
    if (h < 0) return;
    
    int sqrt_h = isqrt(h * PRECISION);
    int t = -b - sqrt_h;
    
    if (t < 20) t = -b + sqrt_h;
    if (t < 20) return;
    
    if (t < rec->t) {
        rec->t = t;
        rec->hit = 1;
        rec->mat_col = s.color;
        rec->reflect = s.reflect;
        rec->p = v_add(ro, v_mul(rd, t));
        rec->n = v_norm(v_sub(rec->p, s.pos));
    }
}

void intersect_plane(Vec3 ro, Vec3 rd, HitRec* rec) {
    int plane_y = -1536;
    
    if (rd.y >= 0) return;
    
    int t = ((plane_y - ro.y) * PRECISION) / rd.y;
    
    if (t < 20 || t > rec->t) return;
    
    rec->t = t;
    rec->hit = 1;
    rec->reflect = 0;
    rec->p = v_add(ro, v_mul(rd, t));
    rec->n = (Vec3){0, PRECISION, 0};
    
    int tx = rec->p.x;
    int tz = rec->p.z;
    int check = ((tx >> 11) + (tz >> 11)) & 1; 
    
    rec->mat_col = check ? 0xFFFFFF : 0x444444;
}

int color_mul(int col, int intensity) {
    if (intensity < 0) intensity = 0;
    if (intensity > PRECISION) intensity = PRECISION;
    
    int r = (col >> 16) & 0xFF;
    int g = (col >> 8) & 0xFF;
    int b = col & 0xFF;
    
    r = (r * intensity) >> PRECISION_SHIFT;
    g = (g * intensity) >> PRECISION_SHIFT;
    b = (b * intensity) >> PRECISION_SHIFT;
    
    return (r << 16) | (g << 8) | b;
}

int color_add(int c1, int c2) {
    int r = ((c1 >> 16) & 0xFF) + ((c2 >> 16) & 0xFF);
    int g = ((c1 >> 8) & 0xFF) + ((c2 >> 8) & 0xFF);
    int b = (c1 & 0xFF) + (c2 & 0xFF);
    if (r > 255) r = 255;
    if (g > 255) g = 255;
    if (b > 255) b = 255;
    return (r << 16) | (g << 8) | b;
}

int trace(Vec3 ro, Vec3 rd, int depth) {
    HitRec rec;
    rec.t = BIG_DIST;
    rec.hit = 0;
    
    intersect_sphere(ro, rd, spheres[0], &rec);
    intersect_sphere(ro, rd, spheres[1], &rec);
    intersect_plane(ro, rd, &rec);
    
    if (!rec.hit) {
        int t = (rd.y + PRECISION) / 2;
        return color_mul(0x87CEEB, t);
    }
    
    Vec3 light_dir = v_norm(v_sub(light_pos, rec.p));
    
    HitRec shadow_rec;
    shadow_rec.t = v_len(v_sub(light_pos, rec.p));
    shadow_rec.hit = 0;
    
    Vec3 shadow_ro = v_add(rec.p, v_mul(rec.n, 50));
    
    intersect_sphere(shadow_ro, light_dir, spheres[0], &shadow_rec);
    intersect_sphere(shadow_ro, light_dir, spheres[1], &shadow_rec);

    int diff = v_dot(rec.n, light_dir);
    if (diff < 0) diff = 0;
    
    if (shadow_rec.hit) {
        diff = diff / 4;
    } else {
        diff += 200;
        if (diff > PRECISION) diff = PRECISION;
    }
    
    int final_color = color_mul(rec.mat_col, diff);
    
    if (rec.reflect > 0 && depth < MAX_DEPTH) {
        int dn = v_dot(rd, rec.n);
        Vec3 reflect_dir = v_sub(rd, v_mul(rec.n, 2 * dn));
        Vec3 reflect_ro = v_add(rec.p, v_mul(rec.n, 20));
        
        int reflect_col = trace(reflect_ro, reflect_dir, depth + 1);
        
        int inv_ref = PRECISION - rec.reflect;
        final_color = color_add(
            color_mul(final_color, inv_ref),
            color_mul(reflect_col, rec.reflect)
        );
    }
    
    return final_color;
}

int main() {
    printf("=== Ray Tracing ===\n");
    screen_init();
    
    spheres[0].pos = (Vec3){0, 0, 4096};
    spheres[0].r = 1024;
    spheres[0].color = 0xFFFFFF;
    spheres[0].reflect = 800;

    spheres[1].pos = (Vec3){-1536, -512, 3500};
    spheres[1].r = 700;
    spheres[1].color = 0xFF0000;
    spheres[1].reflect = 100;

    light_pos = (Vec3){2048, 3072, -1024};

    int frame_cnt = 0;
    int tick = 0;
    
    Vec3 cam_pos = {0, 0, 0};
    
    printf("Start Rendering Loop...\n");
    
    while(1) {
        tick += 10;
        int s = get_sin(tick % 360);
        int c = get_cos(tick % 360);
        light_pos.x = (c * 3000) >> PRECISION_SHIFT;
        light_pos.z = (s * 3000) >> PRECISION_SHIFT;
        
        spheres[1].pos.y = -512 + ((s * 300) >> PRECISION_SHIFT);

        for (int y = 0; y < SCREEN_H; y++) {
            for (int x = 0; x < SCREEN_W; x++) {
                int u = (x - 24) * 30;
                int v = (20 - y) * 30;
                
                Vec3 ray_dir = {u, v, 1024};
                ray_dir = v_norm(ray_dir);
                
                int color = trace(cam_pos, ray_dir, 0);
                
                screen_draw_pixel(x, y, color);
            }
        }
        
        screen_full_refresh();
        
        frame_cnt++;
        printf("Frame: %d\n", frame_cnt);
        
    }
    
    return 0;
}