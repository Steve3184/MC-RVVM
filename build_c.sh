#!/bin/bash
FILE=$1
CROSS_COMPILE=riscv32-unknown-elf-
CC=${CROSS_COMPILE}gcc
OBJCOPY=${CROSS_COMPILE}objcopy

echo "Compiling C runtime and ${FILE}.c..."

$CC -march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector -I. \
    -T linker.ld crt0.s ${FILE}.c -o ${FILE}.elf

if [ $? -ne 0 ]; then exit 1; fi

$OBJCOPY -O binary ${FILE}.elf temp.bin
echo "Generated temp.bin. Size: $(stat -c%s temp.bin) bytes"
python3 src/main.py temp.bin rv_datapack
