"""Open the already-signed-in WeChat through its Windows tray icon.

This intentionally does not start WeChat or call ShowWindow.  Modern WeChat
needs to handle its own tray activation event to restore its rendered content.
"""

from __future__ import annotations

import argparse
import ctypes
import os
import struct
import time
from pathlib import Path
from ctypes import wintypes

from pywinauto import Desktop
from pywinauto.findwindows import ElementNotFoundError


WECHAT_TRAY_NAME = "微信"
TRAY_CLASS = "Shell_TrayWnd"
OVERFLOW_CLASS = "NotifyIconOverflowWindow"
FIND_TIMEOUT_SECONDS = 5
WINDOW_TITLE = "微信"
CF_HDROP = 15
GMEM_MOVEABLE = 0x0002

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# ctypes defaults to 32-bit C ints.  Explicit pointer-sized signatures are
# essential here: GlobalLock returns a 64-bit memory address on this machine.
kernel32.GlobalAlloc.argtypes = (wintypes.UINT, ctypes.c_size_t)
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalLock.argtypes = (wintypes.HGLOBAL,)
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = (wintypes.HGLOBAL,)
kernel32.GlobalUnlock.restype = wintypes.BOOL
kernel32.GlobalFree.argtypes = (wintypes.HGLOBAL,)
kernel32.GlobalFree.restype = wintypes.HGLOBAL
user32.OpenClipboard.argtypes = (wintypes.HWND,)
user32.OpenClipboard.restype = wintypes.BOOL
user32.EmptyClipboard.restype = wintypes.BOOL
user32.SetClipboardData.argtypes = (wintypes.UINT, wintypes.HANDLE)
user32.SetClipboardData.restype = wintypes.HANDLE
user32.CloseClipboard.restype = wintypes.BOOL


def copy_file_to_clipboard(file_path: Path) -> None:
    """Put one existing file onto the Windows clipboard as a file-drop item."""
    # DROPFILES: pFiles (DWORD), pt.x/pt.y (LONG), fNC (BOOL), fWide (BOOL).
    # It is followed by a double-NUL-terminated UTF-16 file path.
    header = struct.pack("<IiiII", 20, 0, 0, 0, 1)
    data = header + os.fspath(file_path).encode("utf-16-le") + b"\0\0\0\0"
    memory = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
    if not memory:
        raise ctypes.WinError(ctypes.get_last_error())
    locked = kernel32.GlobalLock(memory)
    if not locked:
        kernel32.GlobalFree(memory)
        raise ctypes.WinError(ctypes.get_last_error())
    ctypes.memmove(locked, data, len(data))
    kernel32.GlobalUnlock(memory)

    for _ in range(10):
        if user32.OpenClipboard(None):
            break
        time.sleep(0.1)
    else:
        kernel32.GlobalFree(memory)
        raise RuntimeError("Unable to access the Windows clipboard")
    try:
        if not user32.EmptyClipboard():
            raise ctypes.WinError(ctypes.get_last_error())
        # On success, Windows owns the global-memory handle.
        if not user32.SetClipboardData(CF_HDROP, memory):
            raise ctypes.WinError(ctypes.get_last_error())
        memory = None
    finally:
        user32.CloseClipboard()
        if memory:
            kernel32.GlobalFree(memory)


def find_wechat_icon(container):
    """Find only the exact WeChat tray icon, not WeChat Input Method items."""
    for button in container.descendants(control_type="Button"):
        if (button.window_text() or "").strip() == WECHAT_TRAY_NAME:
            return button
    return None


def find_icon_in_main_tray(desktop):
    tray = desktop.window(class_name=TRAY_CLASS)
    tray.wait("exists ready", timeout=FIND_TIMEOUT_SECONDS)
    return find_wechat_icon(tray)


def find_icon_in_overflow(desktop):
    tray = desktop.window(class_name=TRAY_CLASS)
    hidden = tray.child_window(title="显示隐藏的图标", control_type="Button")
    hidden.click_input()

    overflow = desktop.window(class_name=OVERFLOW_CLASS)
    overflow.wait("visible ready", timeout=FIND_TIMEOUT_SECONDS)
    return find_wechat_icon(overflow)


def open_existing_wechat() -> None:
    """Double-click the real tray icon so WeChat restores its own UI state."""
    desktop = Desktop(backend="uia")
    icon = find_icon_in_main_tray(desktop)
    if icon is None:
        icon = find_icon_in_overflow(desktop)
    if icon is None:
        raise RuntimeError("WeChat tray icon was not found. Ensure WeChat is running and signed in.")

    # This is the same action as the user's manual double-click on the tray.
    icon.double_click_input()
    time.sleep(0.5)


def wechat_main_window(desktop):
    """Return the only visible WeChat main window after tray activation."""
    window = desktop.window(title=WINDOW_TITLE, class_name="Qt51514QWindowIcon")
    window.wait("visible ready", timeout=FIND_TIMEOUT_SECONDS)
    return window


def open_chat(friend_name: str) -> None:
    """Search an existing contact and open its first matching chat result.

    This sends no message.  If several contacts have the same display name,
    WeChat's first search result is opened; callers should use a unique remark
    name where possible.
    """
    friend_name = friend_name.strip()
    if not friend_name:
        raise ValueError("friend_name cannot be empty")

    open_existing_wechat()
    desktop = Desktop(backend="uia")
    window = wechat_main_window(desktop)
    window.set_focus()

    # Ctrl+F is WeChat's global contact/chat search shortcut.  The Qt client
    # does not expose the search box through UI Automation, so use its native
    # shortcut instead of fragile screen coordinates.
    window.type_keys("^f")
    time.sleep(0.25)
    window.type_keys(friend_name, with_spaces=True, vk_packet=True)
    time.sleep(0.35)
    window.type_keys("{ENTER}")
    time.sleep(0.4)


def send_message(friend_name: str, message: str) -> None:
    """Open a contact's chat and send one plain-text message.

    This has an external side effect: it sends ``message`` to ``friend_name``.
    Use a unique contact remark where possible, because WeChat opens the first
    search result when duplicate names exist.
    """
    if not message:
        raise ValueError("message cannot be empty")

    open_chat(friend_name)
    desktop = Desktop(backend="uia")
    window = wechat_main_window(desktop)
    window.set_focus()

    # After the search result is opened, WeChat places focus in the chat input.
    # vk_packet preserves Chinese characters, emoji, and spaces as literal text.
    window.type_keys(message, with_spaces=True, vk_packet=True)
    window.type_keys("{ENTER}")


def send_file(friend_name: str, file_name: str | Path) -> None:
    """Open a chat and send one existing file through WeChat.

    This function transmits the specified local file to the selected contact.
    """
    file_path = Path(file_name).expanduser().resolve()
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    open_chat(friend_name)
    copy_file_to_clipboard(file_path)
    desktop = Desktop(backend="uia")
    window = wechat_main_window(desktop)
    window.set_focus()
    window.type_keys("^v")
    time.sleep(0.6)
    window.type_keys("{ENTER}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Open an existing WeChat chat")
    parser.add_argument("friend", nargs="?", help="contact remark/name to search")
    parser.add_argument(
        "--send",
        metavar="MESSAGE",
        help="send MESSAGE after opening the specified contact chat",
    )
    parser.add_argument(
        "--file",
        metavar="PATH",
        help="send the existing local file at PATH after opening the contact chat",
    )
    args = parser.parse_args()
    try:
        if args.send is not None and args.file is not None:
            parser.error("use either --send or --file, not both")
        if args.file is not None:
            if not args.friend:
                parser.error("friend is required when using --file")
            send_file(args.friend, args.file)
            print(f"Sent file to: {args.friend}")
        elif args.send is not None:
            if not args.friend:
                parser.error("friend is required when using --send")
            send_message(args.friend, args.send)
            print(f"Sent message to: {args.friend}")
        elif args.friend:
            open_chat(args.friend)
            print(f"Opened WeChat search result for: {args.friend}")
        else:
            open_existing_wechat()
            print("Sent double-click to the existing WeChat tray icon.")
    except (ElementNotFoundError, TimeoutError) as error:
        raise RuntimeError("Windows notification area is unavailable") from error
