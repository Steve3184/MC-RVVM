#ifndef RCON_H
#define RCON_H

#include <stdint.h>
#include <stddef.h>

#define RCON_TYPE_RESPONSE   0
#define RCON_TYPE_EXEC       2
#define RCON_TYPE_AUTH       3
#define RCON_TYPE_AUTH_FAIL  -1

#define RCON_MAX_PAYLOAD     4096
#define RCON_PACKET_HEADER   12
#define RCON_TIMEOUT_SEC     5

typedef struct {
    int fd;
    int next_id;
} rcon_t;

typedef struct {
    int32_t  size;
    int32_t  id;
    int32_t  type;
    char     payload[RCON_MAX_PAYLOAD + 2];
    int      payload_len;
} rcon_packet_t;

int rcon_connect(rcon_t *r, const char *host, const char *port);
int rcon_auth(rcon_t *r, const char *password);
int rcon_command(rcon_t *r, const char *cmd, char *response, size_t resp_len);
void rcon_close(rcon_t *r);

#endif
