#include "utils.h"

inline void write_hex_fast(char* p, int color) {
    static const char hex[] = "0123456789ABCDEF";
    p[0] = hex[(color >> 20) & 0xF];
    p[1] = hex[(color >> 16) & 0xF];
    p[2] = hex[(color >> 12) & 0xF];
    p[3] = hex[(color >> 8) & 0xF];
    p[4] = hex[(color >> 4) & 0xF];
    p[5] = hex[(color >> 0) & 0xF];
}

static int SIN_LUT[360];

int iabs(int x) { return x < 0 ? -x : x; }

static const int SIN_90[] = {
    0, 18, 36, 54, 71, 89, 107, 125, 143, 160, 178, 195, 213, 230, 248, 265, 282, 299, 316, 333, 
    350, 367, 384, 400, 417, 433, 449, 465, 481, 496, 512, 527, 543, 558, 573, 587, 602, 616, 630, 644, 
    658, 672, 685, 698, 711, 724, 737, 749, 761, 773, 784, 796, 807, 818, 828, 839, 849, 859, 868, 878, 
    887, 895, 904, 912, 920, 928, 935, 943, 950, 957, 963, 970, 976, 982, 987, 993, 998, 1003, 1008, 1012, 
    1016, 1020, 1023, 1026, 1028, 1031, 1032, 1034, 1035, 1036, 1037
};

int get_sin(int d) {
    d %= 360; if (d < 0) d += 360;
    if (d <= 90) return SIN_90[d];
    if (d <= 180) return SIN_90[180 - d];
    if (d <= 270) return -SIN_90[d - 180];
    return -SIN_90[360 - d];
}

int get_cos(int d) {
    return get_sin(d + 90);
}