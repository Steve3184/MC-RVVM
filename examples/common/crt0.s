.section .text.init
.global _start
.global memcpy

_start:
    li sp, 1024
    jal ra, main
    li a7, 93    # dump
    ecall
    li a7, 10    # halt
    ecall

memcpy:
    mv a3, a0
    beqz a2, 2f
1:
    lb t0, 0(a1)
    sb t0, 0(a3)
    addi a1, a1, 1
    addi a3, a3, 1
    addi a2, a2, -1
    bnez a2, 1b
2:
    ret

.global memset
memset:
    mv a3, a0
    beqz a2, 2f
1:
    sb a1, 0(a3)
    addi a3, a3, 1
    addi a2, a2, -1
    bnez a2, 1b
2:
    ret

# UART putchar (a0 = char)
.global putchar
putchar:
    li a7, 11
    ecall
    ret

# UART puts (a0 = str)
.global puts
puts:
    addi sp, sp, -16
    sw ra, 12(sp)
    sw s0, 8(sp)
    mv s0, a0
1:
    lbu a0, 0(s0)
    beqz a0, 2f
    jal ra, putchar
    addi s0, s0, 1
    j 1b
2:
    li a0, 10 # \n
    jal ra, putchar
    lw ra, 12(sp)
    lw s0, 8(sp)
    addi sp, sp, 16
    ret

.global poweroff
poweroff:
    li a7, 12
    li a0, 0x5555
    ecall
    ret

.global exec_cmd
exec_cmd:
    li a7, 14
    ecall
    ret

loop:
    j loop
