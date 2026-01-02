# ⛏️ MC-RVVM: Minecraft 里的高性能 RISC-V 转译器

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Minecraft Version](https://img.shields.io/badge/Minecraft-1.21%2B-green.svg)](https://www.minecraft.net/)
[![Architecture](https://img.shields.io/badge/Arch-RISC--V%20(RV32IMA)-orange.svg)](https://riscv.org/)

[English](README.md) | **简体中文**

**MC-RVVM** 是一套强大的工具链，能将 **RISC-V (RV32IMA)** 机器码静态转译为 Minecraft 原版数据包，它不是一个模拟器，而是让二进制程序间接在 `.mcfunction` 中高速运行的黑科技

想在 Minecraft 里运行 **Linux 内核**？或者跑一个 C 写的 **Doom**？MC-RVVM 让这一切成为可能，且无需任何 Mod，纯原版支持

## ✨ 核心特性

- **⚡ 静态转译技术**: 将 ELF 文件预编译为基于树状分发的 Minecraft 函数，极大减少运行时开销
- **🔧 完整架构支持**: 完美支持 standard RV32IMA 指令集
- **🐧 运行 Linux**: 包含 `mini-rv32ima` 移植，支持在游戏内引导 Linux 6.x 内核（虽然启动非常慢，但那可是完整Linux内核！）
- **🚀 极速寻址优化**: 独有的指令折叠与二分查找优化，大幅提升指令执行速度
- **💻 优秀的 I/O**: 实现了可靠的 UART 输出到聊天栏，支持基本的数据交互
- **📦 开箱即用**: 支持 Minecraft 1.21+ (数据包格式 48)

## 🛠️ 环境要求

要构建本项目，你需要准备以下工具：

1.  **Python 3.x**: 用于运行核心转译器和生成脚本
2.  **RISC-V Toolchain**: 编译 C 代码必须
    *   Ubuntu/Debian: `sudo apt install gcc-riscv64-unknown-elf`
3.  **Device Tree Compiler (dtc)**: 编译 `mini-rv32ima` 及其设备树需要
    *   Ubuntu/Debian: `sudo apt install device-tree-compiler`
4.  **Minecraft Java Edition**: 1.21 或更高版本 (推荐 1.21.1)

## 🚀 性能优化 (高级技巧)

本项目支持通过 GCC 的 `Os` 参数来显著加速代码执行，由于 MC 函数执行指令时的瓶颈在于二分查找跳转，**减小代码体积 (`Os`) 比传统的速度优化 (`O3`) 更能提升性能**

你可以在代码的关键片段中使用以下宏来开启优化：

```c
#pragma GCC push_options
#pragma GCC optimize ("Os")

void my_function() {
    // 这里的代码会被 gcc 优化体积
    // 从而在 Minecraft 中获得更快的寻址速度
}

#pragma GCC pop_options
```

> [!WARNING]
> **注意事项：**
> 1.  **绝对不要**对 `main` 函数或调用了 Native 函数（如 syscalls）的代码使用此优化，否则会导致转译器内存布局错误
> 2.  仅支持**片段指定**，全局开启 `Os` 或其他优化等级 (`O2`/`O3`) 可能会改变内存分布，导致转译失败或运行时崩溃

## 🏁 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/Steve3184/MC-RVVM.git
cd MC-RVVM
```

### 2. 编译示例
`examples/` 目录下提供了多种不同用途的示例

**A. 基础功能测试 (`rvvm_test`)** 最快上手，验证指令集支持度：
```bash
make -C examples/rvvm_test
```

**B. 完整 Linux 模拟器 (`mini-rv32ima`)** 编译全功能模拟器，支持加载外部 Linux 镜像或动态 ELF：
```bash
make -C examples/mini-rv32ima
```

**C. 虚拟机测试 (`vm_baretest`)** **(推荐)** 这是一个用于测试 `mini-rv32ima` 的虚拟内核，如果你只是想看虚拟机跑起来而不必等待漫长的 Linux 启动，请用这个：
```bash
make -C examples/vm_baretest
```

**D. 质数计算压力测试 (`prime`)**
计算 10000 以内的质数，用于高强度的指令吞吐量测试与性能基准评估

<video src="docs_assets/prime_test.webm" controls muted style="max-width: 600px"></video>

编译该测试：
```bash
make -C examples/prime
```

### 3. 安装到 Minecraft
1.  生成的 `rv_datapack` 文件夹就是你的数据包
2.  将其复制到存档的 `datapacks/` 目录下：
    `~/.minecraft/saves/<你的存档>/datapacks/`
3.  进入游戏，输入 `/datapack enable xxx`
4.  看到绿色的 `[MC-RVVM] Loaded.` 即表示加载成功

## 🔨 编译你自己的程序

如果编译自己的 C 程序，需要使用特定的 GCC 参数以确保兼容性：

**必需的 GCC 参数：**
`-march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector`

**必需的链接文件：**
你必须复制 `examples/common` 目录下的 `linker.ld` 和 `crt0.s` 到你的项目目录并参与链接，否则程序无法正确引导

**Makefile 示例：**
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

**转译器参数说明 (`src/main.py`)：**

- `usage: main.py [-h] [--namespace NAMESPACE] input_file output_dir`
- `input_file`: 二进制文件 (.bin) 或 Hex dump 路径
- `output_dir`: 数据包输出目录
- `--namespace`: 数据包命名空间 (默认: `rv32`)

## 🎮 游戏内操作

- **重置/启动**: `/function rv32:reset`
- **Dump所有寄存器**: `/function rv32:debug/dump_inline`
- **手动时钟**: `/function rv32:tick` (正常情况下会自动运行)

### 关于运行 Linux
如果你编译了完整的 `mini-rv32ima` 并想体验启动 Linux：
1.  下载内核镜像 [linux-6.8-rc1-rv32nommu-cnl-1.zip](https://github.com/cnlohr/mini-rv32ima-images/raw/refs/heads/master/images/linux-6.8-rc1-rv32nommu-cnl-1.zip) 并解压出 `Image`
2.  使用工具导入内核：
    ```bash
    python3 img2mc.py Image rv_datapack/data/rv32/function/load_extra_data.mcfunction rv32
    ```
3.  启动虚拟机：`/function rv32:reset`
4.  **注意**：启动 Linux 需要极长的时间（取决于你的 CPU 单核性能），请耐心等待

## 📂 项目结构

- `src/`: 转译器核心
- `examples/`:
    - `rvvm_test`: 基础指令测试
    - `mini-rv32ima`: 完整的 RISC-V 虚拟机实现
    - `vm_baretest`: 测试虚拟机用的虚拟内核
    - `prime`: 质数计算压力测试
    - `common`: 包含 `ld` 配置和内置库实现
- `img2mc.py`: 大文件/内核镜像导入工具
- `rv_datapack/`: 最终生成的数据包

## 📄 许可证

[MIT LICENSE](LICENSE)
