#define _POSIX_C_SOURCE 200112L
#define _XOPEN_SOURCE 500
#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <time.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include "rcon.h"

#define SOCK_MAGIC 0x534F434B
#define NBT_ARRAY_LEN 136

typedef union {
    struct {
        int32_t magic;      // [0]
        int32_t mc_req;     // [1] 1=Bind, 2=Connect, 3=Send, 4=Close
        int32_t host_ack;   // [2] 0=Idle, 1=Success, -1=Error/Closed, 2=RX Ready
        int32_t protocol;   // [3] 0=TCP, 1=UDP
        int32_t ip_addr;    // [4] IPv4 e.g. 0x7F000001
        int32_t port;       // [5] Port number
        int32_t tx_len;     // [6] Bytes in tx_buf (max 256)
        int32_t rx_len;     // [7] Bytes in rx_buf (max 256)
        int32_t tx_buf[64]; // [8..71] Send buffer
        int32_t rx_buf[64]; // [72..135] Receive buffer
    } field;
    int32_t raw[NBT_ARRAY_LEN];
} mc_socket_mem_t;

static int listen_sock = -1;
static int active_sock = -1;

static double now_sec(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static volatile int g_running = 1;
static void on_signal(int sig) {
    (void)sig;
    g_running = 0;
}

static void set_nonblocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags >= 0) fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

static void cleanup_sockets() {
    if (listen_sock >= 0) { close(listen_sock); listen_sock = -1; }
    if (active_sock >= 0) { close(active_sock); active_sock = -1; }
}

static int32_t fetch_nbt_int(rcon_t* rcon, const char* target, int index) {
    char cmd[256];
    char resp[RCON_MAX_PAYLOAD];
    snprintf(cmd, sizeof(cmd), "data get %s[%d]", target, index);
    if (rcon_command(rcon, cmd, resp, sizeof(resp)) < 0) return 0;
    
    char* p = strrchr(resp, ' ');
    if (p) return (int32_t)strtol(p + 1, NULL, 10);
    return 0;
}

static void sync_to_mc(rcon_t* rcon, const char* target, const mc_socket_mem_t* mem, int sync_rx) {
    char cmd[512];
    char resp[RCON_MAX_PAYLOAD];

    snprintf(cmd, sizeof(cmd), "data modify %s[1] set value %d", target, mem->field.mc_req);
    rcon_command(rcon, cmd, resp, sizeof(resp));
    
    snprintf(cmd, sizeof(cmd), "data modify %s[2] set value %d", target, mem->field.host_ack);
    rcon_command(rcon, cmd, resp, sizeof(resp));

    if (sync_rx) {
        snprintf(cmd, sizeof(cmd), "data modify %s[7] set value %d", target, mem->field.rx_len);
        rcon_command(rcon, cmd, resp, sizeof(resp));

        char* big_cmd = malloc(4096);
        int offset = snprintf(big_cmd, 4096, "data modify %s set value [I;", target);
        
        for (int i = 0; i < NBT_ARRAY_LEN; i++) {
            offset += snprintf(big_cmd + offset, 4096 - offset, "%d%s", 
                               mem->raw[i], (i == NBT_ARRAY_LEN - 1) ? "" : ",");
        }
        snprintf(big_cmd + offset, 4096 - offset, "]");
        rcon_command(rcon, big_cmd, resp, sizeof(resp));
        free(big_cmd);
    }
}

static void process_mc_request(mc_socket_mem_t* mem) {
    int req = mem->field.mc_req;
    int proto = mem->field.protocol; // 0=TCP, 1=UDP
    
    struct sockaddr_in sa = {0};
    sa.sin_family = AF_INET;
    sa.sin_addr.s_addr = htonl((uint32_t)mem->field.ip_addr);
    sa.sin_port = htons((uint16_t)mem->field.port);

    mem->field.mc_req = 0;
    int success = 0;

    switch (req) {
        case 1: /* BIND */
            cleanup_sockets();
            listen_sock = socket(AF_INET, (proto == 0) ? SOCK_STREAM : SOCK_DGRAM, 0);
            if (listen_sock >= 0) {
                int opt = 1;
                setsockopt(listen_sock, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
                if (bind(listen_sock, (struct sockaddr*)&sa, sizeof(sa)) == 0) {
                    if (proto == 0) {
                        listen(listen_sock, 1); // TCP
                        set_nonblocking(listen_sock);
                    } else {
                        active_sock = listen_sock; // UDP
                        listen_sock = -1;
                        set_nonblocking(active_sock);
                    }
                    success = 1;
                } else {
                    cleanup_sockets();
                }
            }
            mem->field.host_ack = success ? 1 : -1;
            break;

        case 2: /* CONNECT */
            cleanup_sockets();
            active_sock = socket(AF_INET, (proto == 0) ? SOCK_STREAM : SOCK_DGRAM, 0);
            if (active_sock >= 0) {
                if (connect(active_sock, (struct sockaddr*)&sa, sizeof(sa)) == 0) {
                    set_nonblocking(active_sock);
                    success = 1;
                } else {
                    cleanup_sockets();
                }
            }
            mem->field.host_ack = success ? 1 : -1;
            break;

        case 3: /* SEND */
            if (active_sock >= 0 && mem->field.tx_len > 0 && mem->field.tx_len <= 256) {
                printf("[SEND] Data Len: %d\n", mem->field.tx_len);
                ssize_t sent = send(active_sock, mem->field.tx_buf, mem->field.tx_len, 0);
                if (sent >= 0) success = 1;
            }
            mem->field.host_ack = success ? 1 : -1;
            break;

        case 4: /* CLOSE */
            cleanup_sockets();
            mem->field.host_ack = 1;
            break;
    }
}

static void process_host_receive(mc_socket_mem_t* mem, int* needs_sync) {
    if (mem->field.host_ack != 0) return;

    if (listen_sock >= 0 && active_sock == -1) {
        int client = accept(listen_sock, NULL, NULL);
        if (client >= 0) {
            active_sock = client;
            set_nonblocking(active_sock);
        }
    }

    if (active_sock >= 0) {
        char buffer[256];
        ssize_t r = recv(active_sock, buffer, sizeof(buffer), 0);
        
        if (r > 0) {
            memset(mem->field.rx_buf, 0, sizeof(mem->field.rx_buf));
            memcpy(mem->field.rx_buf, buffer, r);
            mem->field.rx_len = r;
            mem->field.host_ack = 2; /* RX Ready */
            *needs_sync = 1;
        } 
        else if (r == 0) {
            cleanup_sockets();
            mem->field.host_ack = 3; /* ACK_CLOSED */
            *needs_sync = 1;
        }
        else if (r < 0 && errno != EAGAIN && errno != EWOULDBLOCK) {
            cleanup_sockets();
            mem->field.host_ack = -1; /* ACK_ERROR */
            *needs_sync = 1;
        }
    }
}

/* ── Main ── */
int main(int argc, char *argv[])
{
    if (argc < 4) {
        fprintf(stderr,
            "Usage: %s <host> <port> <password> [nbt_target]\n"
            "  host       : RCON server address (e.g. 127.0.0.1)\n"
            "  port       : RCON port           (e.g. 25575)\n"
            "  password   : RCON password\n"
            "  nbt_target : Minecraft NBT path  (default: storage rv32:ram data_socket)\n",
            argv[0]);
        return EXIT_FAILURE;
    }

    const char *host     = argv[1];
    const char *port     = argv[2];
    const char *password = argv[3];
    const char *target   = argc >= 5 ? argv[4] : "storage rv32:ram data_socket";

    signal(SIGINT,  on_signal);
    signal(SIGTERM, on_signal);

    rcon_t rcon = { .fd = -1, .next_id = 1 };

    printf("[*] Connecting to %s:%s …\n", host, port);
    if (rcon_connect(&rcon, host, port) < 0) {
        fputs("[-] Connection failed.\n", stderr);
        return EXIT_FAILURE;
    }
    printf("[*] Authenticating …\n");
    if (rcon_auth(&rcon, password) < 0) {
        fputs("[-] Authentication failed.\n", stderr);
        rcon_close(&rcon);
        return EXIT_FAILURE;
    }
    printf("[+] Authenticated RPC Bridge Active.\n\n");

    mc_socket_mem_t mc_mem = {0};
    
    unsigned long poll_cycles = 0;
    double window_start = now_sec();

    while (g_running) {
        for (int i = 0; i < 8; i++) {
            mc_mem.raw[i] = fetch_nbt_int(&rcon, target, i);
        }

        if (mc_mem.field.magic != SOCK_MAGIC) {
            memset(&mc_mem, 0, sizeof(mc_mem));
            mc_mem.field.magic = SOCK_MAGIC;
            continue;
        }

        int needs_sync = 0;

        if (mc_mem.field.mc_req != 0) {
            if (mc_mem.field.mc_req == 3) {
                for (int i = 8; i < 72; i++) {
                    mc_mem.raw[i] = fetch_nbt_int(&rcon, target, i);
                }
            }
            process_mc_request(&mc_mem);
            needs_sync = 1;
        }
        else if (mc_mem.field.host_ack == 0) {
            process_host_receive(&mc_mem, &needs_sync);
        }

        if (needs_sync) {
            sync_to_mc(&rcon, target, &mc_mem, (mc_mem.field.host_ack == 2));
            
            printf("\r\033[K[EVENT] MC_Req:%d Ack:%d RX:%d TX:%d\n", 
                   mc_mem.field.mc_req, mc_mem.field.host_ack, 
                   mc_mem.field.rx_len, mc_mem.field.tx_len);
        }

        poll_cycles++;
        double elapsed = now_sec() - window_start;
        if (elapsed >= 1.0) {
            double qps = poll_cycles / elapsed;
            printf("\r\033[K[ %4.0f polls/sec ]  %s:%s", 
                   qps, 
                   (mc_mem.field.protocol == 0) ? "TCP" : "UDP", 
                   (active_sock >= 0) ? "CONNECTED" : (listen_sock >= 0 ? "LISTENING" : "IDLE")
                );
            fflush(stdout);
            poll_cycles = 0;
            window_start = now_sec();
        }

        usleep(5000);
    }

    cleanup_sockets();
    rcon_close(&rcon);
    printf("\n\n[*] stopped.\n");
    return EXIT_SUCCESS;
}
