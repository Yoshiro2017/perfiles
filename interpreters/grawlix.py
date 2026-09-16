#!/usr/bin/env python3
"""
!@#$%^&*()_+ Interpreter — Python port
From D source: https://esolangs.org/wiki/!@#$%^&*()_+
Usage: grawlix yourfile.graw
File format: .graw (grawlix)
"""

import sys
import os


def getchar():
    """Read one character; return -1 on EOF"""
    try:
        c = sys.stdin.read(1)
        if not c:
            return -1
        return ord(c)
    except EOFError:
        return -1


class GrawlixState:
    def __init__(self, code):
        self.code = code
        self.ptr = 0
        self.stack = []
        self.jump_positions = {}

        # Initial stack contains a single zero
        self.stack.append(0)

        # Pre-scan and match parentheses
        paren_stack = []
        for idx, char in enumerate(self.code):
            if char == '(':
                paren_stack.append(idx)
            elif char == ')':
                if not paren_stack:
                    raise ValueError("Unmatched parentheses")
                start = paren_stack.pop()
                self.jump_positions[start] = idx
                self.jump_positions[idx] = start

    @property
    def running(self):
        return self.ptr < len(self.code)

    @property
    def top(self):
        if not self.stack:
            self.stack.append(0)
        return self.stack[-1]

    @top.setter
    def top(self, value):
        if not self.stack:
            self.stack.append(0)
        self.stack[-1] = value

    def pop(self):
        if not self.stack:
            return 0
        return self.stack.pop()

    def pop_from(self, index):
        val = self.stack[index]
        del self.stack[index]
        return val

    def info(self):
        """Debug: print stack contents"""
        for idx, val in enumerate(self.stack):
            if 32 <= val <= 126:
                print(f"{idx}: {val} ('{chr(val)})", file=sys.stderr)
            else:
                print(f"{idx}: {val}", file=sys.stderr)

    def step(self):
        char = self.code[self.ptr]
        advance = True

        if char == '!':
            # Duplicate top
            self.stack.append(self.top)

        elif char == '@':
            # Pop and print as Unicode character
            val = self.pop()
            sys.stdout.write(chr(val))
            sys.stdout.flush()

        elif char == '#':
            # Pop and print as integer
            print(self.pop(), end='')
            sys.stdout.flush()

        elif char == '$':
            # Swap top two
            a = self.pop()
            b = self.pop()
            self.stack.append(a)
            self.stack.append(b)

        elif char == '%':
            # Rotate stack 1 right: move top to bottom
            if len(self.stack) > 1:
                top = self.stack.pop()
                self.stack.insert(0, top)

        elif char == '^':
            # Increment top of stack
            self.top += 1

        elif char == '&':
            # Pop index, push that element (0-indexed from bottom)
            idx_raw = self.pop()
            while idx_raw < 0:
                idx_raw += len(self.stack)
            idx = int(idx_raw)
            val = self.pop_from(idx)
            self.stack.append(val)

        elif char == '=':
            # Old indexing: push element without removing it
            idx_raw = self.pop()
            while idx_raw < 0:
                idx_raw += len(self.stack)
            idx = int(idx_raw)
            self.stack.append(self.stack[idx])

        elif char == '?':
            # Debug: print stack info
            self.info()

        elif char == '*':
            # Input char code and add to top
            self.top += getchar()

        elif char == '(':
            # Loop start: jump if top is zero
            if self.top == 0:
                self.ptr = self.jump_positions[self.ptr]

        elif char == ')':
            # Loop end: jump back if top not zero
            self.ptr = self.jump_positions[self.ptr]
            advance = False

        elif char == '_':
            # Negate top
            self.top = -self.top

        elif char == '+':
            # Add top two
            val = self.pop()
            self.top += val

        else:
            # Literal: push Unicode value of character
            self.stack.append(ord(char))

        if advance:
            self.ptr += 1

    def run(self):
        while self.running:
            self.step()


def main():
    if len(sys.argv) != 2:
        print("!@#$%^&*()_+ Interpreter", file=sys.stderr)
        print("Usage: grawlix yourfile.graw", file=sys.stderr)
        sys.exit(1)

    filename = sys.argv[1]

    if not os.path.exists(filename):
        # Treat argument as direct code string
        code = filename
    else:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                code = f.read()
        except PermissionError:
            print(f"Error: No permission to read '{filename}'", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        state = GrawlixState(code)
        state.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
