#ifndef SOCKET_H
#define SOCKET_H

#include <stdint.h>
#include <stddef.h>

#define AF_INET     2
#define SOCK_STREAM 1
#define SOCK_DGRAM  2

#define IPPROTO_TCP 0
#define IPPROTO_UDP 1

typedef uint32_t in_addr_t;
struct in_addr {
    in_addr_t s_addr;
};

struct sockaddr_in {
    uint16_t       sin_family;
    uint16_t       sin_port;
    struct in_addr sin_addr;
    char           sin_zero[8];
};

struct sockaddr {
    uint16_t sa_family;
    char     sa_data[14];
};

typedef int socklen_t;

int socket(int domain, int type, int protocol);
int connect(int sockfd, const struct sockaddr *addr, socklen_t addrlen);
int bind(int sockfd, const struct sockaddr *addr, socklen_t addrlen);
int listen(int sockfd, int backlog);
int accept(int sockfd, struct sockaddr *addr, socklen_t *addrlen);
int send(int sockfd, const void *buf, size_t len, int flags);
int recv(int sockfd, void *buf, size_t len, int flags);
int close(int sockfd);

uint16_t htons(uint16_t hostshort);
uint32_t htonl(uint32_t hostlong);
#define ntohs htons
#define ntohl htonl

#endif
