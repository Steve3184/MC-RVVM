# MC-RVVM (RV32 ELF to Minecraft Compiler)

MC-RVVM is a toolchain that transpiles RISC-V (RV32IMA) machine code into Minecraft Function (`.mcfunction`) commands, allowing static binaries to run natively as a Datapack.

While the core of the project is a transpiler, it also includes a RISC-V Virtual Machine implementation (written in C) as a usage example, demonstrating how to execute complex logic within Minecraft.

## Features

- **Transpiler:** Converts RV32IMA machine code into a tree-based dispatch system in Minecraft.
- **Architecture:** Supports RV32IMA (Integer, Multiply, Atomic).
- **Runtime:** Pure Vanilla Minecraft Datapack (1.21+, Pack Format 48).
- **Example VM:** Includes `mini_rv32ima_mc.c`, a lightweight RISC-V emulator that can run inside Minecraft after transpilation.

## Prerequisites

To build and run this project, you need:

1.  **Python 3.x**: For the transpiler and generator scripts.
2.  **RISC-V Toolchain**: `riscv32-unknown-elf-gcc` is required to compile the C code.
    *   Ubuntu/Debian: `sudo apt install gcc-riscv64-unknown-elf` (ensure 32-bit support or use a specific 32-bit toolchain).
3.  **Minecraft Java Edition**: Version 1.21 or later.

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Steve3184/MC-RVVM.git
cd MC-RVVM
```

### 2. Compile and Generate Datapack
The project includes a build script `build_c.sh` that automates the compilation of the C runtime and the generation of the datapack.

To build the example `mini_rv32ima_mc.c`:

```bash
./build_c.sh mini_rv32ima_mc
```

This script will:
1.  Compile `mini_rv32ima_mc.c` using `riscv32-unknown-elf-gcc`.
2.  Generate a `temp.bin` raw binary.
3.  Run `src/main.py` to transpile the binary into the `rv_datapack` folder.

### 3. Install in Minecraft
1.  Locate your Minecraft saves folder (e.g., `~/.minecraft/saves/<WorldName>/datapacks/` on Linux).
2.  Copy the generated `rv_datapack` folder into the `datapacks` folder of your world.
    ```bash
    cp -r rv_datapack ~/.minecraft/saves/MyWorld/datapacks/
    ```
3.  Open the world in Minecraft.
4.  Run `/datapack enable xxx` to load the datapack.
5.  You should see a generic "[MC-RVVM] Loaded." message.

### 4. (Optional) Running the VM Example
If you are using the `mini_rv32ima_mc.c` emulator to run a guest OS (like Linux), you need to load the kernel image into the datapack.

1.  Compile the emulator as shown above.
2.  Prepare your kernel image file. You can download a pre-built Linux image from here:
    [linux-6.8-rc1-rv32nommu-cnl-1.zip](https://github.com/cnlohr/mini-rv32ima-images/raw/refs/heads/master/images/linux-6.8-rc1-rv32nommu-cnl-1.zip)
    (Extract the `Image` file from the zip).
3.  Run the `img2mc.py` tool to generate the loader function:
    ```bash
    python3 img2mc.py Image rv_datapack/data/rv32/function/mem/load_image_data.mcfunction
    ```
4.  Install/Update the datapack in your world and `/reload`.

## Usage in Game

The emulator initializes automatically upon reload. You can control it using the following trigger or commands (depending on implementation details in `tick.mcfunction`):

- The VM runs automatically via the `tick.mcfunction` loop.
- To reset the VM: `/function rv32:reset`
- Execution halts if the program exits or triggers a halt condition.

## Project Structure

- `src/`: Python source code for the transpiler and instruction decoder.
    - `main.py`: Entry point, generates the datapack structure.
    - `decoder.py`: Decodes raw binary into RISC-V instructions.
    - `transpiler.py`: Converts instructions to `.mcfunction`.
- `mini_rv32ima_mc.c`: The guest C code (RISC-V emulator logic or test program).
- `crt0.s` & `linker.ld`: Bootloader and linker script for the bare-metal RISC-V environment.
- `rv_datapack/`: The output directory for the generated Minecraft Datapack.

## License

[MIT LICENSE](LICENSE)