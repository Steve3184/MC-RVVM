CC      = gcc
CFLAGS  = -Wall -Wextra -O2 -std=c11
TARGET  = mcnetdriver
SRCS    = main.c rcon.c
OBJS    = $(SRCS:.c=.o)

.PHONY: all clean

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) $(CFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	rm -f $(OBJS) $(TARGET)
