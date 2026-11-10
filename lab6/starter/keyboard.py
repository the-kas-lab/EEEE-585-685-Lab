"""Keyboard input for a terminal teleop node (EEEE-585/685 Lab 6).

Copy this file into your package, next to your node. Use it like this:

    with Keyboard() as kb:
        key = kb.get_key()

Inside the `with` block, key presses reach your program one at a time, without
waiting for Enter, and are not echoed. The terminal is put back to normal when
the block ends, even if your code crashes. Ctrl-C still raises
KeyboardInterrupt.

You do not need to change this file.
"""

import os
import select
import sys
import termios
import tty


class Keyboard:

    def __enter__(self):
        if not sys.stdin.isatty():
            raise RuntimeError(
                'keyboard input needs a terminal (with docker run, use -it)')
        self._fd = sys.stdin.fileno()
        self._saved = termios.tcgetattr(self._fd)
        tty.setcbreak(self._fd)
        return self

    def __exit__(self, *exc):
        termios.tcsetattr(self._fd, termios.TCSADRAIN, self._saved)
        return False

    def get_key(self):
        """Return the last key pressed since the previous call, or None.

        Never waits. If several keys arrived since the last call (a held key
        repeats about 30 times per second), they are all consumed and only the
        most recent one is returned, so old key presses do not pile up.
        """
        data = b''
        while select.select([self._fd], [], [], 0)[0]:
            chunk = os.read(self._fd, 64)
            if not chunk:
                break
            data += chunk
        if not data:
            return None
        return data[-1:].decode('ascii', errors='replace')
