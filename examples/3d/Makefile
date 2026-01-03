CC = riscv32-unknown-elf-gcc
OBJCOPY = riscv32-unknown-elf-objcopy
PYTHON = python3

BASE_CFLAGS = -march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector -Os -I. -I../common

GC_CFLAGS = -ffunction-sections -fdata-sections

LDFLAGS = -Wl,--gc-sections -Wl,--entry=_start -T $(LDSCRIPT)

LDSCRIPT = ../common/linker.ld
CRT0 = ../common/crt0.s
MAIN_PY = ../../src/main.py
DATAPACK_DIR = ../../rv_datapack

COMMON_OBJS = crt0.o utils.o screen.o

.PHONY: all clean 3dmaze 3drtx 3dcube transpile_maze transpile_rtx transpile_cube

all: 3dmaze 3drtx 3dcube

3dmaze: transpile_maze
	@:

3dmaze.elf: $(COMMON_OBJS) 3dmaze.o
	$(CC) $(BASE_CFLAGS) $(LDFLAGS) $(COMMON_OBJS) 3dmaze.o -o $@

3dmaze.bin: 3dmaze.elf
	$(OBJCOPY) -O binary $< $@

transpile_maze: 3dmaze.bin
	$(PYTHON) $(MAIN_PY) $< $(DATAPACK_DIR)

3dcube: transpile_cube
	@:

3dcube.elf: $(COMMON_OBJS) 3dcube.o
	$(CC) $(BASE_CFLAGS) $(LDFLAGS) $(COMMON_OBJS) 3dcube.o -o $@

3dcube.bin: 3dcube.elf
	$(OBJCOPY) -O binary $< $@

transpile_cube: 3dcube.bin
	$(PYTHON) $(MAIN_PY) $< $(DATAPACK_DIR)

3drtx: transpile_rtx
	@:

3drtx.elf: $(COMMON_OBJS) 3drtx.o
	$(CC) $(BASE_CFLAGS) $(LDFLAGS) $(COMMON_OBJS) 3drtx.o -o $@

3drtx.bin: 3drtx.elf
	$(OBJCOPY) -O binary $< $@

transpile_rtx: 3drtx.bin
	$(PYTHON) $(MAIN_PY) $< $(DATAPACK_DIR)

3dmaze.o: 3dmaze.c
	$(CC) $(BASE_CFLAGS) -c $< -o $@

3dcube.o: 3dcube.c
	$(CC) $(BASE_CFLAGS) -c $< -o $@

3drtx.o: 3drtx.c
	$(CC) $(BASE_CFLAGS) -c $< -o $@

crt0.o: $(CRT0)
	$(CC) $(BASE_CFLAGS) -c $< -o $@

utils.o: utils.c
	$(CC) $(BASE_CFLAGS) $(GC_CFLAGS) -c $< -o $@

screen.o: screen.c
	$(CC) $(BASE_CFLAGS) $(GC_CFLAGS) -c $< -o $@

clean:
	rm -f *.elf *.bin *.o