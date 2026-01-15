# ⛏️ MC-RVVM

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Minecraft Version](https://img.shields.io/badge/Minecraft-1.21%2B-green.svg)](https://www.minecraft.net/)
[![Architecture](https://img.shields.io/badge/Arch-RISC--V%20(RV32IMA)-orange.svg)](https://riscv.org/)

[English](README.md) | **简体中文**

![Linux Boot](docs_assets/linux.webp)

**MC-RVVM** 是一个强大的工具链，能够将 **RISC-V (RV32IMA)** 机器码静态转译为原版 Minecraft 数据包 它不仅仅是一个模拟器，而是一场“黑魔法”，让二进制程序能够间接地在 `.mcfunction` 文件中高速运行

<details>
<summary><b>工作原理</b></summary>

MC-RVVM 通过将 RISC-V 机器码 (ELF/bin) 静态转译为 Minecraft 的 `.mcfunction` 文件来工作

1.  **内存模拟**：使用 `scoreboard` (计分板) 和 `storage` 来模拟 32 位寄存器和 RAM
2.  **指令调度**：生成一个二叉搜索树 (BST)，以便根据程序计数器 (PC) 高效地跳转到正确的指令函数
3.  **块优化**：将连续的指令合并为单个函数块，以尽量减少调度开销，显著提升性能

</details>

想在 Minecraft 里运行 **Linux 内核**吗？或者玩玩用 C 语言写的 **Doom**？MC-RVVM 让这一切在纯原版环境下成为可能——无需任何模组

## ✨ 核心特性

- **⚡ 静态转译**：将 ELF 文件预编译为基于树结构的 Minecraft 函数，极大地减少了运行时开销
- **🚀 块优化**：自动识别热点代码并进行指令块优化，显著降低调度深度并提高效率（使用 `--optimize`）
- **📺 GPU 渲染引擎**：具备基于 `text_display` 的高速渲染功能，支持 48x40 分辨率输出
- **💤 原子睡眠 (Atomic Sleep)**：完整支持 `sleep` 系统调用，允许暂停指定时长或暂停后续指令的执行
- **🔧 全架构支持**：完美支持标准的 RV32IMA 指令集
- **🐧 运行 Linux**：包含了 `mini-rv32ima` 的移植版本，允许你在游戏内启动 Linux 6.x 内核（启动虽慢，但它是真正的 Linux 内核！）
- **🚀 快速寻址**：具有独特的指令折叠和二叉搜索优化，显著提升执行速度
- **💻 优秀的 I/O**：实现了可靠的串口 (UART) 输出到聊天栏，并支持基本的数据交互
- **📦 开箱即用**：支持 Minecraft 1.21+（数据包格式 48）

## 🛠️ 环境要求

构建本项目需要以下工具：

1.  **Python 3.x**：用于运行核心转译器和生成脚本
2.  **RISC-V 工具链**：编译 C 代码所需
    *   Ubuntu/Debian：`sudo apt install gcc-riscv64-unknown-elf`
3.  **设备树编译器 (dtc)**：编译 `mini-rv32ima` 及其设备树所需
    *   Ubuntu/Debian：`sudo apt install device-tree-compiler`
4.  **Minecraft Java 版**：1.21 或更高版本（推荐 1.21.1）

## 🚀 性能优化（高级）

本项目支持使用 GCC 的 `Os` 标志来加速代码执行 由于 MC 函数执行的瓶颈通常在于寻址时的二叉搜索跳转，**减小代码体积 (`Os`) 通常比传统速度优化 (`O3`) 效果更好**

目前已全面支持并**强烈推荐**全局优化 使用 `-Os` 配合 `-ffunction-sections` 和 `-fdata-sections` 可以让转译器更好地处理代码结构并提高寻址效率

> [!TIP]
> **为什么选择 Os？**
> 在 Minecraft 中，程序计数器 (PC) 的跳转是通过深层的函数二叉搜索树实现的 更小的二进制体积意味着更少的“页”和更浅的跳转深度，这会直接转化为更高的每刻指令数 (IPT)

## 🏁 快速入门

### 1. 克隆仓库
```bash
git clone https://github.com/Steve3184/MC-RVVM.git
cd MC-RVVM
```

### 2. 编译示例
`examples/` 目录包含用于不同目的的各种示例

<details open>
<summary><b>可用示例列表</b></summary>

#### **A. Linux 模拟器 (`examples/mini-rv32ima`)**
一个能够启动 Linux 的完整 RISC-V 模拟器
- **速度**：约 980 指令/秒 (Guest)
- **启动时间**：约 3 分钟显示首条 kmsg，完整启动约需 9 小时
- **注意**：目前仅可见早期内核输出；`init` 后的 UART 输出暂不可用
```bash
make -C examples/mini-rv32ima
```

#### **B. 3D 渲染 (`examples/3d`, `examples/fast3d`)**
各种 3D 渲染演示，包括立方体、迷宫和光线追踪 (RTX)
```bash
make -C examples/3d
# 或者使用优化版本
make -C examples/fast3d
```

#### **C. 素数测试 (`examples/prime`)**
计算高达 10,000 的素数的压力测试
```bash
make -C examples/prime
```

#### **D. 基础测试 (`examples/rvvm_test`, `examples/vm_baretest`)**
- `rvvm_test`：基础指令集验证
- `vm_baretest`：裸机 VM 测试（推荐用于不启动 Linux 时的快速 VM 功能测试）
```bash
make -C examples/rvvm_test
make -C examples/vm_baretest
```

#### **E. 屏幕/显示 (`examples/screen`)**
显示渲染引擎测试

</details>

### 3. 安装到 Minecraft
1.  生成的 `rv_datapack` 文件夹即为你的数据包
2.  将其复制到存档的 `datapacks/` 目录：
    `~/.minecraft/saves/<存档名称>/datapacks/`
3.  进入游戏并运行 `/datapack enable xxx`
4.  看到绿色的 `[MC-RVVM] Loaded.` 消息即表示成功

## 🔨 编译你自己的程序

要编译你自己的 C 程序，必须使用特定的 GCC 标志以确保兼容性：

**必需的 GCC 标志：**
`-march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector -fno-jump-tables`

**必需的链接文件：**
你必须从 `examples/common` 目录复制 `linker.ld` 和 `crt0.s` 到你的项目文件夹并进行链接；否则程序将无法正常启动

**Makefile 示例：**
```makefile
CC = riscv32-unknown-elf-gcc
OBJCOPY = riscv32-unknown-elf-objcopy
PYTHON = python3

CFLAGS = -march=rv32ima -mabi=ilp32 -nostdlib -fno-builtin -fno-stack-protector -ffunction-sections -fdata-sections -fno-jump-tables -I. -Os
LDSCRIPT = linker.ld
CRT0 = crt0.s

MAIN_PY = src/main.py
DATAPACK_DIR = rv_datapack

TARGET = my_program

all: $(TARGET).bin transpile

$(TARGET).elf: $(TARGET).c $(CRT0)
	$(CC) $(CFLAGS) -Wl,-Map=$(TARGET).map -T $(LDSCRIPT) $(CRT0) $(TARGET).c -o $@

$(TARGET).bin: $(TARGET).elf
	$(OBJCOPY) -O binary $< $@

transpile: $(TARGET).bin
	$(PYTHON) $(MAIN_PY) $< $(DATAPACK_DIR) --map_file $(TARGET).map -O

clean:
	rm -f *.elf *.bin *.map
```

**转译器参数 (`src/main.py`)：**

- `用法: main.py [-h] [--namespace NAMESPACE] [--map_file MAP_FILE] [--optimize] [--ipt IPT] 输入文件 输出目录`
- `input_file`：二进制文件 (.bin) 或十六进制转储文件的路径
- `output_dir`：数据包的输出目录
- `--namespace`：数据包命名空间（默认：`rv32`）
- `--optimize` / `-O`：启用块优化，显著提升复杂程序的运行速度
- `--ipt`：设置每刻指令数（默认：2500，最大：3200）
- `--map_file`：指定 GCC 生成的 `.map` 文件，让块优化器能够识别函数边界

## 🎮 游戏内操作

- **重置/开始**：`/function rv32:reset`
- **转储所有寄存器**：`/function rv32:debug/dump_inline`
- **手动 Tick**：`/function rv32:tick`（正常情况下会自动运行）

### 运行 Linux
如果你编译了完整的 `mini-rv32ima` 并想尝试启动 Linux：
1.  下载内核镜像 [linux-6.8-rc1-rv32nommu-cnl-1.zip](https://github.com/cnlohr/mini-rv32ima-images/raw/refs/heads/master/images/linux-6.8-rc1-rv32nommu-cnl-1.zip) 并解压出 `Image`
2.  使用工具导入内核：
    ```bash
    python3 img2mc.py Image rv_datapack/data/rv32/function/load_extra_data.mcfunction rv32
    ```
3.  启动虚拟机：`/function rv32:reset`
4.  **注意**：启动 Linux 需要非常长的时间（取决于你的单核 CPU 性能），请耐心等待

## 📂 项目结构

- `src/`：核心转译器文件
- `examples/`：
    - `rvvm_test`：基础指令测试
    - `mini-rv32ima`：完整的 RISC-V 虚拟机实现
    - `vm_baretest`：用于虚拟机测试的虚拟内核
    - `prime`：素数计算压力测试
    - `common`：包含 `ld` 配置和内置库实现
- `img2mc.py`：用于导入大型文件/内核镜像的工具
- `rv_datapack/`：最终生成的数据包

## 📄 许可证

[MIT License](LICENSE)