#define _POSIX_C_SOURCE 200112L
#include "rcon.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <netdb.h>

static int32_t le32(int32_t v)
{
#if __BYTE_ORDER__ == __ORDER_BIG_ENDIAN__
    return (int32_t)(
        ((uint32_t)v >> 24) |
        (((uint32_t)v >> 8)  & 0x0000FF00u) |
        (((uint32_t)v << 8)  & 0x00FF0000u) |
        ((uint32_t)v << 24));
#else
    return v;
#endif
}

static int read_exact(int fd, void *buf, size_t n)
{
    size_t done = 0;
    char  *p    = (char *)buf;
    while (done < n) {
        fd_set rfds;
        struct timeval tv = { RCON_TIMEOUT_SEC, 0 };
        FD_ZERO(&rfds);
        FD_SET(fd, &rfds);
        int rc = select(fd + 1, &rfds, NULL, NULL, &tv);
        if (rc < 0) {
            if (errno == EINTR) return -1;
            return -1;
        }
        if (rc == 0) {
            errno = ETIMEDOUT;
            return -1;
        }
        ssize_t r = read(fd, p + done, n - done);
        if (r < 0 && errno == EINTR) continue;
        if (r <= 0) return -1;
        done += (size_t)r;
    }
    return 0;
}

static int write_exact(int fd, const void *buf, size_t n)
{
    size_t      done = 0;
    const char *p    = (const char *)buf;
    while (done < n) {
        ssize_t w = write(fd, p + done, n - done);
        if (w < 0 && errno == EINTR) continue;
        if (w <= 0) return -1;
        done += (size_t)w;
    }
    return 0;
}

static int send_packet(int fd, int32_t id, int32_t type, const char *payload)
{
    int     plen  = payload ? (int)strlen(payload) : 0;
    int32_t size  = 10 + plen;
    uint8_t buf[14 + RCON_MAX_PAYLOAD];

    if (plen > RCON_MAX_PAYLOAD) return -1;

    int32_t ws = le32(size);
    int32_t wi = le32(id);
    int32_t wt = le32(type);

    memcpy(buf,      &ws, 4);
    memcpy(buf + 4,  &wi, 4);
    memcpy(buf + 8,  &wt, 4);
    if (plen) memcpy(buf + 12, payload, plen);
    buf[12 + plen]     = '\0';
    buf[12 + plen + 1] = '\0';

    return write_exact(fd, buf, (size_t)(12 + plen + 2));
}

static int recv_packet(int fd, rcon_packet_t *pkt)
{
    uint8_t hdr[12];
    if (read_exact(fd, hdr, 12) < 0) return -1;

    int32_t size, id, type;
    memcpy(&size, hdr,     4);
    memcpy(&id,   hdr + 4, 4);
    memcpy(&type, hdr + 8, 4);

    pkt->size = le32(size);
    pkt->id   = le32(id);
    pkt->type = le32(type);

    int body = pkt->size - 10;
    if (body < 0 || body > RCON_MAX_PAYLOAD) return -1;

    uint8_t tmp[RCON_MAX_PAYLOAD + 2];
    if (read_exact(fd, tmp, (size_t)(body + 2)) < 0) return -1;

    memcpy(pkt->payload, tmp, (size_t)body);
    pkt->payload[body] = '\0';
    pkt->payload_len   = body;

    return 0;
}

int rcon_connect(rcon_t *r, const char *host, const char *port)
{
    struct addrinfo hints = { 0 }, *res, *rp;
    hints.ai_family   = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    int err = getaddrinfo(host, port, &hints, &res);
    if (err) return -1;

    int fd = -1;
    for (rp = res; rp; rp = rp->ai_next) {
        fd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (fd < 0) continue;
        if (connect(fd, rp->ai_addr, rp->ai_addrlen) == 0) break;
        close(fd);
        fd = -1;
    }
    freeaddrinfo(res);

    if (fd < 0) return -1;

    r->fd      = fd;
    r->next_id = 1;
    return 0;
}

int rcon_auth(rcon_t *r, const char *password)
{
    int32_t id = r->next_id++;

    if (send_packet(r->fd, id, RCON_TYPE_AUTH, password ? password : "") < 0) return -1;

    rcon_packet_t pkt;
    for (int tries = 0; tries < 3; tries++) {
        if (recv_packet(r->fd, &pkt) < 0) return -1;
        if (pkt.type == RCON_TYPE_EXEC || pkt.type == RCON_TYPE_RESPONSE) {
            if (pkt.type == RCON_TYPE_EXEC) break;
        }
    }

    if (pkt.id == -1 || pkt.id == RCON_TYPE_AUTH_FAIL) return -1;
    return 0;
}

int rcon_command(rcon_t *r, const char *cmd, char *response, size_t resp_len)
{
    int32_t id = r->next_id++;

    if (send_packet(r->fd, id, RCON_TYPE_EXEC, cmd) < 0) return -1;

    rcon_packet_t pkt;
    if (recv_packet(r->fd, &pkt) < 0) return -1;

    int copy = pkt.payload_len < (int)resp_len - 1 ? pkt.payload_len : (int)resp_len - 1;
    memcpy(response, pkt.payload, copy);
    response[copy] = '\0';
    return copy;
}

void rcon_close(rcon_t *r)
{
    if (r && r->fd >= 0) {
        close(r->fd);
        r->fd = -1;
    }
}