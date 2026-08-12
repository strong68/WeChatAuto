"""Windows clipboard helpers for file-drop payloads."""

from __future__ import annotations

import ctypes
import os
import struct
import time
from ctypes import wintypes
from pathlib import Path

from wechat_auto.constants import CF_HDROP, GMEM_MOVEABLE


class FileClipboard:
    """Copy files as Windows ``CF_HDROP`` clipboard content."""

    def __init__(self, open_attempts: int = 10, retry_delay: float = 0.1) -> None:
        self.open_attempts = open_attempts
        self.retry_delay = retry_delay
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._configure_api()

    def _configure_api(self) -> None:
        """Declare pointer-sized signatures required by 64-bit Windows."""
        self.kernel32.GlobalAlloc.argtypes = (wintypes.UINT, ctypes.c_size_t)
        self.kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        self.kernel32.GlobalLock.argtypes = (wintypes.HGLOBAL,)
        self.kernel32.GlobalLock.restype = ctypes.c_void_p
        self.kernel32.GlobalUnlock.argtypes = (wintypes.HGLOBAL,)
        self.kernel32.GlobalUnlock.restype = wintypes.BOOL
        self.kernel32.GlobalFree.argtypes = (wintypes.HGLOBAL,)
        self.kernel32.GlobalFree.restype = wintypes.HGLOBAL
        self.user32.OpenClipboard.argtypes = (wintypes.HWND,)
        self.user32.OpenClipboard.restype = wintypes.BOOL
        self.user32.EmptyClipboard.restype = wintypes.BOOL
        self.user32.SetClipboardData.argtypes = (wintypes.UINT, wintypes.HANDLE)
        self.user32.SetClipboardData.restype = wintypes.HANDLE
        self.user32.CloseClipboard.restype = wintypes.BOOL

    @staticmethod
    def build_dropfiles_payload(file_path: Path) -> bytes:
        """Create a Unicode ``DROPFILES`` header and one terminated path."""
        header = struct.pack("<IiiII", 20, 0, 0, 0, 1)
        return header + os.fspath(file_path).encode("utf-16-le") + b"\0\0\0\0"

    def copy_file(self, file_path: Path) -> None:
        """Place one existing file onto the clipboard as a file-drop item."""
        payload = self.build_dropfiles_payload(file_path)
        memory = self.kernel32.GlobalAlloc(GMEM_MOVEABLE, len(payload))
        if not memory:
            raise ctypes.WinError(ctypes.get_last_error())

        locked = self.kernel32.GlobalLock(memory)
        if not locked:
            self.kernel32.GlobalFree(memory)
            raise ctypes.WinError(ctypes.get_last_error())
        ctypes.memmove(locked, payload, len(payload))
        self.kernel32.GlobalUnlock(memory)

        if not self._open_clipboard():
            self.kernel32.GlobalFree(memory)
            raise RuntimeError("Unable to access the Windows clipboard")
        try:
            if not self.user32.EmptyClipboard():
                raise ctypes.WinError(ctypes.get_last_error())
            if not self.user32.SetClipboardData(CF_HDROP, memory):
                raise ctypes.WinError(ctypes.get_last_error())
            memory = None  # Windows owns the handle after SetClipboardData.
        finally:
            self.user32.CloseClipboard()
            if memory:
                self.kernel32.GlobalFree(memory)

    def _open_clipboard(self) -> bool:
        for _ in range(self.open_attempts):
            if self.user32.OpenClipboard(None):
                return True
            time.sleep(self.retry_delay)
        return False
