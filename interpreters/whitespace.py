#!/usr/bin/env python3

# Whitespace Interpreter — Python implementation
# Compatible: Linux, macOS, Termux, Windows
# Usage: whitespace yourfilename.ws
# Spec: SP=' ', HT='\t', LF='\n'


import sys
import os

# ── Character constants ──────────────────────────────────
SP = ' '
HT = '\t'
LF = '\n'

# ── Custom Exception Classes ──────────────────────────────
class WhitespaceSyntaxError(Exception):
    """Raised when program structure is invalid"""
    pass

class WhitespaceRuntimeError(Exception):
    """Raised during execution: stack empty, invalid jump, etc."""
    pass

class WhitespaceEOFError(Exception):
    """Raised when code ends unexpectedly"""
    pass

class WhitespaceError(Exception):
    """Base error class"""
    pass


class WhitespaceInterpreter:
    def __init__(self):
        self.tokens = []
        self.pc = 0               # Program counter
        self.stack = []           # Main data stack
        self.heap = {}            # Heap memory {address: value}
        self.labels = {}          # Label cache {label_string: pc_position}
        self.call_stack = []      # Subroutine return stack
        self.running = False

    # ── Tokenization ──────────────────────────────────────
    def tokenize(self, source):
        """Keep only SP/HT/LF; discard all other characters (including comments)"""
        return [c for c in source if c in (SP, HT, LF)]

    # ── Low-level helpers ──────────────────────────────────
    def fetch(self, n=1):
        """Get next n tokens, advance pc; raise EOF if missing"""
        end = self.pc + n
        if end > len(self.tokens):
            raise WhitespaceEOFError(
                f"Unexpected end of program at position {self.pc} "
                f"(need {n} more token{'s' if n!=1 else ''})"
            )
        chunk = self.tokens[self.pc:end]
        self.pc = end
        return chunk

    def peek(self, n=1):
        """Look ahead without advancing; return None if out of bounds"""
        if self.pc + n > len(self.tokens):
            return None
        return self.tokens[self.pc:self.pc+n]

    # ── Parsers ────────────────────────────────────────────
    def parse_number(self):
        """Format: sign + binary digits + LF"""
        if not self.tokens:
            raise WhitespaceSyntaxError("Empty program — nothing to parse")

        sign_tok, = self.fetch()
        if sign_tok == SP:
            sign = 1
        elif sign_tok == HT:
            sign = -1
        else:
            raise WhitespaceSyntaxError(
                f"Expected sign [SP] or [HT] for number, got {repr(sign_tok)}"
            )

        value = 0
        digits = 0
        while self.peek() != [LF]:
            if self.peek() is None:
                raise WhitespaceEOFError("Unterminated number — missing [LF]")
            bit, = self.fetch()
            if bit == SP:
                value = (value << 1) | 0
            elif bit == HT:
                value = (value << 1) | 1
            else:
                raise WhitespaceSyntaxError(f"Invalid digit token: {repr(bit)}")
            digits += 1

        self.pc += 1  # consume terminating LF
        return sign * value

    def parse_label(self):
        """Label = [SP/HT] sequence ending with [LF]"""
        label_chars = []
        while self.peek() != [LF]:
            if self.peek() is None:
                raise WhitespaceSyntaxError("Unterminated label — missing [LF]")
            c, = self.fetch()
            if c not in (SP, HT):
                raise WhitespaceSyntaxError(f"Label may only contain [SP]/[HT], got {repr(c)}")
            label_chars.append(c)
        self.pc += 1  # consume LF
        label_str = ''.join(label_chars)
        return label_str

    # ── Pre-scan all labels ────────────────────────────────
    def cache_labels(self):
        """Find all label positions before execution (enables forward jumps)"""
        saved_pc = self.pc
        self.pc = 0
        while self.pc < len(self.tokens):
            if self.peek(2) == [LF, SP]:
                self.pc += 2
                lbl = self.parse_label()
                if lbl in self.labels:
                    raise WhitespaceSyntaxError(f"Duplicate label defined: {repr(lbl)}")
                self.labels[lbl] = self.pc
            else:
                self.pc += 1
        self.pc = saved_pc

    # ── Stack Operations ───────────────────────────────────
    def pop_check(self, name="operation"):
        """Pop with underflow check"""
        if not self.stack:
            raise WhitespaceRuntimeError(f"Stack empty — cannot pop for {name}")
        return self.stack.pop()

    def peek_check(self, name="operation"):
        """Peek top with underflow check"""
        if not self.stack:
            raise WhitespaceRuntimeError(f"Stack empty — cannot peek for {name}")
        return self.stack[-1]

    def nth_check(self, n, name="operation"):
        """Get nth-from-top with bounds check"""
        if n < 0:
            raise WhitespaceRuntimeError(f"Index cannot be negative (got {n}) in {name}")
        if n >= len(self.stack):
            raise WhitespaceRuntimeError(
                f"Index {n} out of range — stack has only {len(self.stack)} items in {name}"
            )
        return self.stack[-1 - n]

    # ── Operation Handlers ─────────────────────────────────
    def handle_stack(self):
        """[SP] — Stack Manipulation"""
        self.pc += 1
        cmd = self.fetch()
        if cmd == [SP]:
            val = self.parse_number()
            self.stack.append(val)

        elif cmd == [LF]:
            sub = self.fetch()
            if sub == [SP]:
                # Duplicate top
                val = self.peek_check("duplicate")
                self.stack.append(val)
            elif sub == [HT]:
                # Swap top two
                if len(self.stack) < 2:
                    raise WhitespaceRuntimeError("Need at least 2 items to swap")
                a, b = self.stack[-2], self.stack[-1]
                self.stack[-2], self.stack[-1] = b, a
            elif sub == [LF]:
                # Discard top
                self.pop_check("discard")
            else:
                raise WhitespaceSyntaxError(f"Unknown stack subcommand: [LF]+{repr(sub)}")

        elif cmd == [HT]:
            sub = self.fetch()
            n = self.parse_number()
            if sub == [SP]:
                # Copy nth to top
                val = self.nth_check(n, "copy-nth")
                self.stack.append(val)
            elif sub == [LF]:
                # Slide: keep top, remove n below
                if n < 1:
                    raise WhitespaceRuntimeError(f"Slide count must be ≥ 1 (got {n})")
                if len(self.stack) < n + 1:
                    raise WhitespaceRuntimeError(
                        f"Slide {n} needs {n+1} items, stack has {len(self.stack)}"
                    )
                keep = self.stack[-1]
                self.stack = self.stack[:-n-1] + [keep]
            else:
                raise WhitespaceSyntaxError(f"Unknown stack subcommand: [HT]+{repr(sub)}")
        else:
            raise WhitespaceSyntaxError(f"Unknown stack command: {repr(cmd)}")

    def handle_arithmetic(self):
        """[HT][SP] — Arithmetic"""
        self.pc += 2
        op = self.fetch()
        b = self.pop_check("arithmetic (right operand)")
        a = self.pop_check("arithmetic (left operand)")

        if op == [SP]:
            self.stack.append(a + b)
        elif op == [HT]:
            self.stack.append(a - b)
        elif op == [LF]:
            self.stack.append(a * b)
        elif op == [SP] and self.tokens[self.pc-3] == HT:
            # Division: [HT][SP][HT][SP]
            if b == 0:
                raise WhitespaceRuntimeError("Division by zero")
            self.stack.append(int(a // b))
        elif op == [HT] and self.tokens[self.pc-3] == HT:
            # Modulo: [HT][SP][HT][HT]
            if b == 0:
                raise WhitespaceRuntimeError("Modulo by zero")
            self.stack.append(a % b)
        else:
            raise WhitespaceSyntaxError(f"Unknown arithmetic operator: {repr(op)}")

    def handle_heap(self):
        """[HT][HT] — Heap Access"""
        self.pc += 2
        sub = self.fetch()
        if sub == [SP]:
            val = self.pop_check("heap store (value)")
            addr = self.pop_check("heap store (address)")
            self.heap[addr] = val
        elif sub == [HT]:
            addr = self.pop_check("heap retrieve")
            self.stack.append(self.heap.get(addr, 0))
        else:
            raise WhitespaceSyntaxError(f"Unknown heap command: {repr(sub)}")

    def handle_io(self):
        """[HT][LF] — Input/Output"""
        self.pc += 2
        sub = self.fetch()
        if sub == [SP]:
            sub2 = self.fetch()
            if sub2 == [SP]:
                # Output char
                val = self.pop_check("output char")
                try:
                    sys.stdout.write(chr(val))
                    sys.stdout.flush()
                except ValueError:
                    raise WhitespaceRuntimeError(f"Value {val} is not a valid Unicode character")
            elif sub2 == [HT]:
                # Output number
                val = self.pop_check("output number")
                sys.stdout.write(str(val))
                sys.stdout.flush()
            else:
                raise WhitespaceSyntaxError(f"Unknown output type: {repr(sub2)}")

        elif sub == [HT]:
            sub2 = self.fetch()
            addr = self.pop_check("input (heap address)")
            if sub2 == [SP]:
                # Read char
                char = sys.stdin.read(1)
                self.heap[addr] = ord(char) if char else 0
            elif sub2 == [HT]:
                # Read integer
                line = sys.stdin.readline()
                try:
                    self.heap[addr] = int(line.strip()) if line.strip() else 0
                except ValueError:
                    raise WhitespaceRuntimeError(f"Expected integer input, got: {repr(line)}")
            else:
                raise WhitespaceSyntaxError(f"Unknown input type: {repr(sub2)}")
        else:
            raise WhitespaceSyntaxError(f"Unknown I/O command: {repr(sub)}")

    def handle_flow(self):
        """[LF] — Flow Control"""
        self.pc += 1
        sub1 = self.fetch()

        if sub1 == [LF]:
            sub2 = self.fetch()
            if sub2 == [LF]:
                # Exit
                self.running = False
            elif sub2 == [HT]:
                # Return from subroutine
                if not self.call_stack:
                    raise WhitespaceRuntimeError("Return called but no active subroutine")
                self.pc = self.call_stack.pop()
            return

        # Commands with label parameter
        label = self.parse_label()
        if label not in self.labels:
            raise WhitespaceRuntimeError(f"Jump/call to undefined label: {repr(label)}")
        target = self.labels[label]

        if sub1 == [SP]:
            sub2 = self.fetch()
            if sub2 == [SP]:
                # Mark label — already cached, do nothing
                pass
            elif sub2 == [HT]:
                # Call subroutine
                self.call_stack.append(self.pc)
                self.pc = target
            elif sub2 == [LF]:
                # Jump unconditional
                self.pc = target
            else:
                raise WhitespaceSyntaxError(f"Unknown flow command: [SP]+{repr(sub2)}")

        elif sub1 == [HT]:
            sub2 = self.fetch()
            top = self.peek_check("conditional jump")
            if sub2 == [SP] and top == 0:
                self.pc = target
            elif sub2 == [HT] and top < 0:
                self.pc = target
            # else: fall through, do nothing

        else:
            raise WhitespaceSyntaxError(f"Unknown flow command: {repr(sub1)}")

    # ── Main Execution ─────────────────────────────────────
    def run(self, source):
        self.tokens = self.tokenize(source)

        if not self.tokens:
            raise WhitespaceSyntaxError("Program contains only comments — no executable code")

        self.pc = 0
        self.stack = []
        self.heap = {}
        self.call_stack = []
        self.labels = {}
        self.running = True

        self.cache_labels()

        while self.running and self.pc < len(self.tokens):
            peek = self.peek()
            if peek == [SP]:
                self.handle_stack()
            elif peek == [HT]:
                peek2 = self.peek(2)
                if peek2 is None:
                    raise WhitespaceEOFError("Incomplete command starting with [HT]")
                _, second = peek2
                if second == SP:
                    self.handle_arithmetic()
                elif second == HT:
                    self.handle_heap()
                elif second == LF:
                    self.handle_io()
                else:
                    raise WhitespaceSyntaxError(f"Unknown IMP: [HT]+{repr(second)}")
            elif peek == [LF]:
                self.handle_flow()
            else:
                raise WhitespaceSyntaxError(f"Invalid token at pc={self.pc}: {repr(peek)}")


# ── Command Line Interface ───────────────────────────────

def main():
    if len(sys.argv) != 2:
        print("Whitespace Interpreter", file=sys.stderr)
        print("Usage: whitespace yourfilename.ws", file=sys.stderr)
        sys.exit(1)

    filename = sys.argv[1]

    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found!", file=sys.stderr)
        sys.exit(1)

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source = f.read()
    except PermissionError:
        print(f"Error: No permission to read '{filename}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading '{filename}': {e}", file=sys.stderr)
        sys.exit(1)

    ws = WhitespaceInterpreter()
    try:
        ws.run(source)
    except WhitespaceSyntaxError as e:
        print(f"[SYNTAX ERROR] {e}", file=sys.stderr)
        sys.exit(2)
    except WhitespaceRuntimeError as e:
        print(f"[RUNTIME ERROR] {e}", file=sys.stderr)
        sys.exit(3)
    except WhitespaceEOFError as e:
        print(f"[EOF ERROR] {e}", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print(f"[UNEXPECTED ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(5)


if __name__ == "__main__":
    main()
