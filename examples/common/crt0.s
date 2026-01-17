.global _start
.global memcpy
.global memset
.global sleep
.global print_int
.global halt
.global putchar
.global puts
.global poweroff
.global load_data
.global exec_cmd
.global screen_init
.global screen_flush
.global read_nbt
.global write_nbt
.global strlen
.global strcpy
.global strcmp
.global str_append
.global itoa_append
.global fmt_coord
.global printf
.global sleep
.global getchar
.global read_buffer

.section .text.init, "ax"
.balign 4
_start:
    li sp, 65536
    jal ra, main
    li a7, 10
    ecall

.section .text.sleep, "ax"
.balign 4
sleep:
    li a7, 25
    ecall
    ret

.section .text.memcpy, "ax"
.balign 4
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

.section .text.memset, "ax"
.balign 4
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

.section .text.print_int, "ax"
.balign 4
print_int:
    li a7, 1
    ecall
    ret

.section .text.halt, "ax"
.balign 4
halt:
    li a7, 10
    ecall
    ret

.section .text.putchar, "ax"
.balign 4
putchar:
    li a7, 11
    ecall
    ret

.section .text.puts, "ax"
.balign 4
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
    li a0, 10
    jal ra, putchar
    lw ra, 12(sp)
    lw s0, 8(sp)
    addi sp, sp, 16
    ret

.section .text.getchar, "ax"
.balign 4
getchar:
    li a7, 26
    ecall
    ret

.section .text.read_buffer, "ax"
.balign 4
read_buffer:
    mv t1, a0
    mv t2, a1
    li t3, 0
    li t5, -1

    addi t4, t2, -1
    blez t4, readloop_end
readloop_start:
    li a7, 26
    ecall

    beq a0, t5, readloop_end

    sb a0, 0(t1)

    addi t1, t1, 1
    addi t3, t3, 1
    addi t2, t2, -1

    li t4, 1
    ble t2, t4, readloop_end

    j readloop_start
readloop_end:
    sb zero, 0(t1)
    
    mv a0, t3
    ret

.section .text.poweroff, "ax"
.balign 4
poweroff:
    li a7, 12
    li a0, 0x5555
    ecall
    ret

.section .text.load_data, "ax"
.balign 4
load_data:
    li a7, 13
    ecall
    ret

.section .text.exec_cmd, "ax"
.balign 4
exec_cmd:
    addi sp, sp, -16
    sw ra, 12(sp)
    sw s0, 8(sp)
    mv s0, a0
    call strlen
    li t0, 256
    bgt a0, t0, 1f
    mv a0, s0
    li a7, 18
    ecall
    j 6f
1:
    li t0, 512
    bgt a0, t0, 2f
    mv a0, s0
    li a7, 19
    ecall
    j 6f
2:
    li t0, 1024
    bgt a0, t0, 3f
    mv a0, s0
    li a7, 20
    ecall
    j 6f
3:
    li t0, 2048
    bgt a0, t0, 4f
    mv a0, s0
    li a7, 21
    ecall
    j 6f
4:
    li t0, 3072
    bgt a0, t0, 5f
    mv a0, s0
    li a7, 22
    ecall
    j 6f
5:
    mv a0, s0
    li a7, 14
    ecall
6:
    lw s0, 8(sp)
    lw ra, 12(sp)
    addi sp, sp, 16
    ret

.section .text.screen_init, "ax"
.balign 4
screen_init:
    li a7, 24
    ecall
    ret

.section .text.screen_flush, "ax"
.balign 4
screen_flush:
    li a7, 23
    ecall
    ret

.section .text.read_nbt, "ax"
.balign 4
read_nbt:
    li a7, 15
    ecall
    ret

.section .text.write_nbt, "ax"
.balign 4
write_nbt:
    li a7, 16
    ecall
    ret

.section .text.strlen, "ax"
.balign 4
strlen:
    mv t0, a0
1:
    lb t1, 0(t0)
    beqz t1, 2f
    addi t0, t0, 1
    j 1b
2:
    sub a0, t0, a0
    ret

.section .text.strcpy, "ax"
.balign 4
strcpy:
    mv t0, a0
1:
    lb t1, 0(a1)
    sb t1, 0(a0)
    beqz t1, 2f
    addi a0, a0, 1
    addi a1, a1, 1
    j 1b
2:
    mv a0, t0
    ret

.section .text.strcmp, "ax"
.balign 4
strcmp:
1:
    lbu t0, 0(a0)
    lbu t1, 0(a1)
    sub t2, t0, t1
    bnez t2, 2f
    beqz t0, 3f
    addi a0, a0, 1
    addi a1, a1, 1
    j 1b
2:
    mv a0, t2
    ret
3:
    li a0, 0
    ret

.section .text.str_append, "ax"
.balign 4
str_append:
1:
    lbu t0, 0(a1)
    beqz t0, 2f
    sb t0, 0(a0)
    addi a0, a0, 1
    addi a1, a1, 1
    j 1b
2:
    ret

.section .text.itoa_append, "ax"
.balign 4
itoa_append:
    mv t0, a0
    mv t1, a1
    bnez t1, 1f
    li t2, 48
    sb t2, 0(t0)
    addi a0, t0, 1
    ret
1:
    bgez t1, 2f
    li t2, 45
    sb t2, 0(t0)
    addi t0, t0, 1
    neg t1, t1
2:
    addi sp, sp, -16
    mv t2, sp
    li t3, 10
3:
    rem t4, t1, t3
    div t1, t1, t3
    addi t4, t4, 48
    sb t4, 0(t2)
    addi t2, t2, 1
    bnez t1, 3b
4:
    addi t2, t2, -1
    lb t4, 0(t2)
    sb t4, 0(t0)
    addi t0, t0, 1
    bne t2, sp, 4b
    addi sp, sp, 16
    mv a0, t0
    ret

.section .text.fmt_coord, "ax"
.balign 4
fmt_coord:
    addi sp, sp, -8
    sw ra, 0(sp)
    sw s0, 4(sp)
    mv t0, a0
    mv s0, a1
    bgez s0, 1f
    li t2, 45
    sb t2, 0(t0)
    addi t0, t0, 1
    neg s0, s0
1:
    li t2, 1000
    div a1, s0, t2
    mv a0, t0
    call itoa_append
    mv t0, a0
    li t3, 46
    sb t3, 0(t0)
    addi t0, t0, 1
    li t2, 1000
    rem a1, s0, t2
    li t2, 100
    div t3, a1, t2
    addi t3, t3, 48
    sb t3, 0(t0)
    addi t0, t0, 1
    li t2, 100
    rem a1, a1, t2
    li t2, 10
    div t3, a1, t2
    addi t3, t3, 48
    sb t3, 0(t0)
    addi t0, t0, 1
    li t2, 10
    rem a1, a1, t2
    addi t3, a1, 48
    sb t3, 0(t0)
    addi t0, t0, 1
    mv a0, t0
    lw s0, 4(sp)
    lw ra, 0(sp)
    addi sp, sp, 8
    ret

.section .text.printf, "ax"
.balign 4
printf:
    addi    sp, sp, -64
    sw      ra, 56(sp)
    sw      s0, 52(sp)
    sw      s1, 48(sp)
    sw      a1, 20(sp)
    sw      a2, 24(sp)
    sw      a3, 28(sp)
    sw      a4, 32(sp)
    sw      a5, 36(sp)
    sw      a6, 40(sp)
    sw      a7, 44(sp)
    mv      s0, a0
    addi    s1, sp, 20

fmt_loop:
    lbu     a0, 0(s0)
    beqz    a0, fmt_end
    addi    s0, s0, 1
    li      t0, 37
    beq     a0, t0, fmt_spec
    call    putchar
    j       fmt_loop

fmt_spec:
    lbu     t0, 0(s0)
    beqz    t0, fmt_end
    addi    s0, s0, 1
    lw      a0, 0(s1)
    addi    s1, s1, 4
    li      t1, 115
    beq     t0, t1, do_str
    li      t1, 100
    beq     t0, t1, do_int
    li      t1, 117
    beq     t0, t1, do_uint
    li      t1, 120
    beq     t0, t1, do_hex
    j       fmt_loop

do_str:
    mv      t5, a0
    beqz    t5, fmt_loop
1:
    lbu     a0, 0(t5)
    beqz    a0, fmt_loop
    addi    sp, sp, -4
    sw      t5, 0(sp)
    call    putchar
    lw      t5, 0(sp)
    addi    sp, sp, 4
    addi    t5, t5, 1
    j       1b

do_int:
    bge     a0, zero, do_uint
    neg     a0, a0
    addi    sp, sp, -4
    sw      a0, 0(sp)
    li      a0, 45
    call    putchar
    lw      a0, 0(sp)
    addi    sp, sp, 4

do_uint:
    li      a1, 10
    j       num_convert

do_hex:
    li      a1, 16
    j       num_convert

num_convert:
    mv      t0, sp
    mv      t1, t0

convert_loop:
    remu    t2, a0, a1
    divu    a0, a0, a1
    li      t3, 10
    blt     t2, t3, 1f
    addi    t2, t2, 39
1:
    addi    t2, t2, 48
    sb      t2, 0(t1)
    addi    t1, t1, 1
    bnez    a0, convert_loop

print_rev:
    addi    t1, t1, -1
    lbu     a0, 0(t1)
    addi    sp, sp, -8
    sw      t0, 0(sp)
    sw      t1, 4(sp)
    call    putchar
    lw      t1, 4(sp)
    lw      t0, 0(sp)
    addi    sp, sp, 8
    bne     t1, t0, print_rev
    j       fmt_loop

fmt_end:
    lw      ra, 56(sp)
    lw      s0, 52(sp)
    lw      s1, 48(sp)
    addi    sp, sp, 64
    ret