#include "socket.h"
#include "crt0.h"

#define SOCKET_MEM_ADDR 0xfd0a0000
#define SOCK_MAGIC      0x534F434B

#define REQ_IDLE    0
#define REQ_BIND    1
#define REQ_CONNECT 2
#define REQ_SEND    3
#define REQ_CLOSE   4

#define ACK_IDLE    0
#define ACK_OK      1
#define ACK_ERROR   -1
#define ACK_RX_DATA 2
#define ACK_CLOSED  3

typedef struct {
    int32_t magic;
    int32_t mc_req;
    volatile int32_t host_ack;
    int32_t protocol;
    int32_t ip_addr;
    int32_t port;
    int32_t tx_len;
    int32_t rx_len;
    int32_t tx_buf[64];
    int32_t rx_buf[64];
} mc_socket_mem_t;

static volatile mc_socket_mem_t *hw = (volatile mc_socket_mem_t *)SOCKET_MEM_ADDR;

static void wait_ack() {
    while (hw->host_ack == ACK_IDLE) { }
}

static void hw_ready() {
    hw->mc_req = REQ_IDLE;
    hw->host_ack = ACK_IDLE;
}

uint16_t htons(uint16_t v) {
    return (uint16_t)((v << 8) | (v >> 8));
}

uint32_t htonl(uint32_t v) {
    return ((v & 0xff000000) >> 24) |
           ((v & 0x00ff0000) >> 8)  |
           ((v & 0x0000ff00) << 8)  |
           ((v & 0x000000ff) << 24);
}

int socket(int domain, int type, int protocol) {
    (void)domain; (void)protocol;
    hw->magic = SOCK_MAGIC;
    hw_ready();
    
    if (type == SOCK_STREAM) hw->protocol = 0;
    else if (type == SOCK_DGRAM) hw->protocol = 1;
    else return -1;

    return 0;
}

int connect(int sockfd, const struct sockaddr *addr, socklen_t addrlen) {
    if (sockfd != 0) return -1;
    const struct sockaddr_in *sin = (const struct sockaddr_in *)addr;

    hw_ready();
    hw->ip_addr = ntohl(sin->sin_addr.s_addr);
    hw->port = ntohs(sin->sin_port);
    hw->mc_req = REQ_CONNECT;

    wait_ack();
    int res = (hw->host_ack == ACK_OK) ? 0 : -1;
    hw_ready();
    return res;
}

int bind(int sockfd, const struct sockaddr *addr, socklen_t addrlen) {
    if (sockfd != 0) return -1;
    const struct sockaddr_in *sin = (const struct sockaddr_in *)addr;

    hw_ready();
    hw->ip_addr = ntohl(sin->sin_addr.s_addr);
    hw->port = ntohs(sin->sin_port);
    hw->mc_req = REQ_BIND;

    wait_ack();
    int res = (hw->host_ack == ACK_OK) ? 0 : -1;
    hw_ready();
    return res;
}

int listen(int sockfd, int backlog) {
    (void)backlog;
    if (sockfd != 0) return -1;
    return 0;
}

int accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen) {
    if (sockfd != 0) return -1;
    return 0;
}

int send(int sockfd, const void *buf, size_t len, int flags) {
    (void)flags;
    if (sockfd != 0) return -1;
    if (len > 256) len = 256;

    hw_ready();
    memcpy((void*)hw->tx_buf, buf, len);
    hw->tx_len = len;
    hw->mc_req = REQ_SEND;

    wait_ack();
    int res = (hw->host_ack == ACK_OK) ? (int)len : -1;
    hw_ready();
    return res;
}

int recv(int sockfd, void *buf, size_t len, int flags) {
    (void)flags;
    if (sockfd != 0) return -1;

    while (hw->host_ack != ACK_RX_DATA) {
        if (hw->host_ack == ACK_ERROR) {
            hw->host_ack = ACK_IDLE;
            return -1;
        }
        if (hw->host_ack == ACK_CLOSED) {
            hw->host_ack = ACK_IDLE;
            return 0;
        }
    }

    int rlen = hw->rx_len;
    if (rlen > (int)len) rlen = (int)len;
    memcpy(buf, (void*)hw->rx_buf, rlen);

    hw->host_ack = ACK_IDLE;
    return rlen;
}

int close(int sockfd) {
    if (sockfd != 0) return -1;
    hw_ready();
    hw->mc_req = REQ_CLOSE;
    wait_ack();
    hw_ready();
    return 0;
}
