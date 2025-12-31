# MC-RVVM (RV32 ELF 到 Minecraft 的编译器 )

MC-RVVM 是一个将 RISC-V (RV32IMA) 机器码静态转译为 Minecraft 函数 (`.mcfunction`) 命令的工具链，使得静态二进制文件能够以数据包的形式在原版游戏中运行

虽然项目的核心是一个转译器，但它也包含了一个用 C 语言编写的 RISC-V 虚拟机实现作为使用示例，展示了如何在 Minecraft 中执行复杂的逻辑

## 功能特性

- **转译器**: 将 RV32IMA 机器码转换为基于树状分发系统的 Minecraft 函数
- **架构支持**: 支持 RV32IMA (Integer, Multiply, Atomic) 指令集
- **运行环境**: 纯原版 Minecraft 数据包 (1.21+, 资源包格式 48)
- **示例 VM**: 包含 `mini_rv32ima_mc.c`，一个轻量级的 RISC-V 模拟器示例，转译后可在 Minecraft 内运行

## 环境要求

构建和运行本项目需要：

1.  **Python 3.x**: 用于运行转译器和生成脚本
2.  **RISC-V 工具链**: 需要 `riscv32-unknown-elf-gcc` 来编译 C 代码
    *   Ubuntu/Debian: `sudo apt install gcc-riscv64-unknown-elf` (请确保支持 32 位或使用特定的 32 位工具链)
3.  **Minecraft Java 版**: 版本 1.21 或更高

## 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/Steve3184/MC-RVVM.git
cd MC-RVVM
```

### 2. 编译并生成数据包
项目包含一个构建脚本 `build_c.sh`，可自动完成 C 运行时的编译和数据包的生成

构建示例 `mini_rv32ima_mc.c`:

```bash
./build_c.sh mini_rv32ima_mc
```

该脚本将执行以下操作：
1.  使用 `riscv32-unknown-elf-gcc` 编译 `mini_rv32ima_mc.c`
2.  生成 `temp.bin` 原始二进制文件
3.  运行 `src/main.py` 将二进制文件转译并输出到 `rv_datapack` 文件夹中

### 3. 安装到 Minecraft
1.  找到你的 Minecraft 存档文件夹 (例如 `~/.minecraft/saves/<存档名>/datapacks/`)
2.  将生成的 `rv_datapack` 文件夹复制到你存档的 `datapacks` 文件夹中
    ```bash
    cp -r rv_datapack ~/.minecraft/saves/MyWorld/datapacks/
    ```
3.  打开你的 Minecraft 世界
4.  输入 `/datapack enable xxx` 命令加载数据包
5.  你应该会看到绿色的 "[MC-RVVM] Loaded." 提示信息

### 4. (可选) 运行 VM 示例
如果你使用 `mini_rv32ima_mc.c` 模拟器来运行系统（如 Linux），你需要将内核镜像加载到数据包中

1.  如上所述编译模拟器
2.  准备内核镜像文件。你可以从此处下载预构建的 Linux 镜像：
    [linux-6.8-rc1-rv32nommu-cnl-1.zip](https://github.com/cnlohr/mini-rv32ima-images/raw/refs/heads/master/images/linux-6.8-rc1-rv32nommu-cnl-1.zip)
    (从压缩包中解压出 `Image` 文件)
3.  运行 `img2mc.py` 工具生成加载函数：
    ```bash
    python3 img2mc.py Image rv_datapack/data/rv32/function/mem/load_image_data.mcfunction
    ```
4.  安装/更新世界中的数据包并 `/reload`

## 游戏内使用

模拟器在重载后会自动初始化

- 虚拟机通过 `tick.mcfunction` 循环自动运行
- 重置虚拟机: `/function rv32:reset`
- 如果程序退出或触发停机条件，执行将停止

## 项目结构

- `src/`: 转译器和指令解码器的 Python 源代码
    - `main.py`: 主程序，负责生成数据包结构
    - `decoder.py`: 将原始二进制解码为 RISC-V 指令
    - `transpiler.py`: 将指令转换为 `.mcfunction`
- `mini_rv32ima_mc.c`: 访客 C 代码 (RISC-V 模拟器逻辑或测试程序)
- `crt0.s` & `linker.ld`: 裸机 RISC-V 环境的启动代码和链接脚本
- `rv_datapack/`: 生成的 Minecraft 数据包输出目录

## 许可证

[MIT LICENSE](LICENSE)
