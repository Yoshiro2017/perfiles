; Hello, World! — x86-64 Linux NASM
; Uses direct kernel system calls — no libc required

section .data
    msg db  "Hello, world!", 0xA   ; Message + newline
    len equ $ - msg                ; Calculate length

section .text
    global _start

_start:
    ; write(1, msg, len)
    mov     rax, 1          ; System call number: write
    mov     rdi, 1          ; File descriptor: stdout = 1
    mov     rsi, msg        ; Pointer to string
    mov     rdx, len        ; Length of string
    syscall

    ; exit(0)
    mov     rax, 60         ; System call number: exit
    mov     rdi, 0          ; Exit status: success = 0
    syscall
