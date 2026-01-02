# ⛏️ MC-RVVM: High-Performance RISC-V Transpiler in Minecraft

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Minecraft Version](https://img.shields.io/badge/Minecraft-1.21%2B-green.svg)](https://www.minecraft.net/)
[![Architecture](https://img.shields.io/badge/Arch-RISC--V%20(RV32IMA)-orange.svg)](https://riscv.org/)

**English** | [简体中文](README_CN.md)

**MC-RVVM** is a powerful toolchain capable of statically transpiling **RISC-V (RV32IMA)** machine code into vanilla Minecraft datapacks. It's not just an emulator; it's a piece of "black magic" that allows binary programs to run at high speed indirectly within `.mcfunction` files.

Want to run the **Linux Kernel** inside Minecraft? Or play **Doom** written in C? MC-RVVM makes all of this possible with pure vanilla support—no mods required.

## ✨ Core Features

- **⚡ Static Transpilation**: Pre-compiles ELF files into tree-based Minecraft functions, drastically reducing runtime overhead.
- **🔧 Full Architecture Support**: Perfectly supports the standard RV32IMA instruction set.
- **🐧 Run Linux**: Includes a port of `mini-rv32ima`, allowing you to boot Linux 6.x kernels in-game (it's slow to boot, but it's a real Linux kernel!).
- **🚀 Fast Addressing**: Features unique instruction folding and binary search optimization, significantly boosting execution speed.
- **💻 Excellent I/O**: Implements reliable UART output to the chat bar and supports basic data interaction.
- **📦 Out of the Box**: Supports Minecraft 1.21+ (Datapack format 48).

## 🛠️ Requirements

To build this project, you will need the following tools:

1.  **Python 3.x**: For running the core transpiler and generation scripts.
2.  **RISC-V Toolchain**: Required for compiling C code.
    *   Ubuntu/Debian: `sudo apt install gcc-riscv64-unknown-elf`
3.  **Device Tree Compiler (dtc)**: Required for compiling `mini-rv32ima` and its device tree.
    *   Ubuntu/Debian: `sudo apt install device-tree-compiler`
4.  **Minecraft Java Edition**: 1.21 or higher (1.21.1 recommended).

## 🚀 Performance Optimization (Advanced)

This project supports accelerating code execution using GCC's `Os` flag. Since the bottleneck in MC function execution is often the binary search jumps for addressing, **reducing code size (`Os`) often yields better performance than traditional speed optimization (`O3`).**

You can enable optimization for critical code sections using the following macros:

```c
#pragma GCC push_options
#pragma GCC optimize ("Os")

void my_function() {
    // This code will be optimized for size,
    // resulting in faster addressing speed in Minecraft.
}

#pragma GCC pop_options
```

> [!WARNING]
> **Notes:**
> 1.  **NEVER** use this optimization on the `main` function or code that calls Native functions (like syscalls), as it causes memory layout errors in the transpiler.
> 2.  Only support **specific segments**. Enabling `Os` or other optimization levels (`O2`/`O3`) globally may alter memory distribution, leading to transpilation failure or runtime crashes.

## 🏁 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Steve3184/MC-RVVM.git
cd MC-RVVM
```

### 2. Compile Examples
The `examples/` directory contains various examples for different purposes.

**A. Basic Functional Test (`rvvm_test`)**
The quickest way to start and verify instruction set support:
```bash
make -C examples/rvvm_test
```

**B. Full Linux Emulator (`mini-rv32ima`)**
Compiles the full-featured emulator, supporting external Linux images or dynamic ELFs:
```bash
make -C examples/mini-rv32ima
```

**C. VM Baretest (`vm_baretest`)** **(Recommended)**
A virtual kernel used to test `mini-rv32ima`. If you just want to see the VM running without waiting for the long Linux boot process, use this:
```bash
make -C examples/vm_baretest
```

**D. Prime Calculation Stress Test (`prime`)**
Calculates primes up to 10,000. Used for high-intensity instruction throughput testing and benchmarking.

<video src="docs_assets/prime_test.webm" controls muted style="max-width: 600px"></video>

Compile this test:
```bash
make -C examples/prime
```

### 3. Install to Minecraft
1.  The generated `rv_datapack` folder is your datapack.
2.  Copy it to your save's `datapacks/` directory:
    `~/.minecraft/saves/<Your_Save>/datapacks/`
3.  Enter the game and run `/datapack enable xxx`.
4.  Seeing the green `[MC-RVVM] Loaded.` message indicates success.

## 🔨 Compiling Your Own Programs

To compile your own C programs, you must use specific GCC flags to ensure compatibility:

**Required GCC Flags:**
`-march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector`

**Required Linker Files:**
You must copy `linker.ld` and `crt0.s` from the `examples/common` directory to your project folder and link them; otherwise, the program will not boot correctly.

**Example Makefile:**
```makefile
CC = riscv32-unknown-elf-gcc
OBJCOPY = riscv32-unknown-elf-objcopy
PYTHON = python3

CFLAGS = -march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector -I. -I../common
LDSCRIPT = linker.ld
CRT0 = crt0.s

MAIN_PY = src/main.py
DATAPACK_DIR = rv_datapack

TARGET = my_program

all: $(TARGET).bin transpile

$(TARGET).elf: $(TARGET).c $(CRT0)
	$(CC) $(CFLAGS) -T $(LDSCRIPT) $(CRT0) $(TARGET).c -o $@

$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@

transpile: $(TARGET).bin
	$(PYTHON) $(MAIN_PY) $< $(DATAPACK_DIR)

clean:
	rm -f *.elf *.bin
```

**Transpiler Arguments (`src/main.py`):**

- `usage: main.py [-h] [--namespace NAMESPACE] input_file output_dir`
- `input_file`: Path to the binary file (.bin) or hex dump.
- `output_dir`: Output directory for the datapack.
- `--namespace`: Datapack namespace (Default: `rv32`).

## 🎮 In-Game Operations

- **Reset/Start**: `/function rv32:reset`
- **Dump All Registers**: `/function rv32:debug/dump_inline`
- **Manual Tick**: `/function rv32:tick` (Runs automatically under normal conditions)

### Running Linux
If you compiled the full `mini-rv32ima` and want to try booting Linux:
1.  Download the kernel image [linux-6.8-rc1-rv32nommu-cnl-1.zip](https://github.com/cnlohr/mini-rv32ima-images/raw/refs/heads/master/images/linux-6.8-rc1-rv32nommu-cnl-1.zip) and extract `Image`.
2.  Import the kernel using the tool:
    ```bash
    python3 img2mc.py Image rv_datapack/data/rv32/function/load_extra_data.mcfunction rv32
    ```
3.  Start the VM: `/function rv32:reset`
4.  **Note**: Booting Linux takes a very long time (depending on your single-core CPU performance). Please be patient.

## 📂 Project Structure

- `src/`: Core transpiler files.
- `examples/`:
    - `rvvm_test`: Basic instruction tests.
    - `mini-rv32ima`: Complete RISC-V VM implementation.
    - `vm_baretest`: Virtual kernel for VM testing.
    - `prime`: Prime calculation stress test.
    - `common`: Contains `ld` config and built-in library implementations.
- `img2mc.py`: Tool for importing large files/kernel images.
- `rv_datapack/`: The final generated datapack.

## 📄 License

[MIT LICENSE](LICENSE)