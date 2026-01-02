.section .text.entry
.global _start
_start:
    .option push
    .option norelax
    la sp, _stack_top       # 确保加载的是链接脚本定义的 0x8000xxxx
    .option pop

    # a0, a1, a2 已经由模拟器设置好
    # a0 = hartid
    # a1 = dtb_pa
    # a2 = dtb_pa (兼容性)
    jal ra, main            # 跳转到 main(a0, a1, a2)
1:  j 1b                   # main 退出后的死循环
