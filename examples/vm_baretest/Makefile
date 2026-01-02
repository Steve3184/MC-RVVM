CC = riscv32-unknown-elf-gcc
OBJCOPY = riscv32-unknown-elf-objcopy
PYTHON = python3

# Flags provided by user
CFLAGS = -march=rv32ima -mabi=ilp32 -static -mcmodel=medany \
         -fvisibility=hidden -nostdlib -nostartfiles
LDSCRIPT = linker.ld

IMG2MC = ../../img2mc.py
DATAPACK_DIR = ../../rv_datapack

SRCS = entry.S main.c
ELF = kernel.elf
BIN = kernel.bin

all: $(BIN) transpile

$(ELF): $(SRCS) $(LDSCRIPT)
	$(CC) $(CFLAGS) -T $(LDSCRIPT) $(SRCS) -o $(ELF)

$(BIN): $(ELF)
	$(OBJCOPY) -O binary $(ELF) $(BIN)

transpile: $(BIN)
	@echo "Transpiling program to Minecraft Datapack..."
	$(PYTHON) $(IMG2MC) $(BIN) $(DATAPACK_DIR)/data/rv32/function/load_extra_data.mcfunction rv32

clean:
	rm -f $(ELF) $(BIN)

.PHONY: all clean transpile