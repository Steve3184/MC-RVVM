#include "../common/socket.h"
#include "../common/crt0.h"

// 127.0.0.1
#define HOST_IP 0x7F000001
#define HOST_PORT 8080

const char *http_req = "GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n";

int main() {
    printf("[MC-RVVM] Socket HTTP Test (Unix-style)\n");
    
    int fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) {
        printf("Socket creation failed\n");
        return 1;
    }
    
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(HOST_PORT);
    addr.sin_addr.s_addr = htonl(HOST_IP);

    printf("Connecting to %d.%d.%d.%d:%d...\n", 
        (HOST_IP >> 24) & 0xFF, (HOST_IP >> 16) & 0xFF, (HOST_IP >> 8) & 0xFF, HOST_IP & 0xFF, 
        HOST_PORT);

    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) {
        printf("Connection failed.\n");
        return 1;
    }
    
    printf("Connected.\n");
    printf("Sending HTTP Request:\n%s\n", http_req);
    
    int sent = send(fd, http_req, strlen(http_req), 0);
    if (sent < 0) {
        printf("Send failed.\n");
        close(fd);
        return 1;
    }
    printf("Sent %d bytes.\n", sent);
    
    printf("Waiting for response...\n");
    char buf[257];
    int total_len = 0;
    int len;
    
    while ((len = recv(fd, buf, 256, 0)) > 0) {
        buf[len] = 0;
        printf("%s", buf);
        total_len += len;
    }
    
    if (len < 0) {
        printf("\nReceive error.\n");
    } else {
        printf("\nReceived total %d bytes.\n", total_len);
    }
    
    close(fd);
    printf("Closed.\n");
    
    return 0;
}