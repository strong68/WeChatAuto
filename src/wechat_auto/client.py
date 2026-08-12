"""High-level WeChat desktop workflows."""

from __future__ import annotations

import time
from pathlib import Path

from pywinauto import Desktop

from wechat_auto.clipboard import FileClipboard
from wechat_auto.constants import WECHAT_WINDOW_CLASS, WECHAT_WINDOW_TITLE
from wechat_auto.exceptions import WeChatWindowNotFoundError
from wechat_auto.tray import WeChatTray


class WeChatClient:
    """Automate a running and already-signed-in Windows WeChat client."""

    def __init__(
        self,
        desktop: Desktop | None = None,
        clipboard: FileClipboard | None = None,
        timeout: float = 5,
    ) -> None:
        self.desktop = desktop or Desktop(backend="uia")
        self.clipboard = clipboard or FileClipboard()
        self.timeout = timeout
        self.tray = WeChatTray(self.desktop, timeout=timeout)

    def open(self) -> None:
        """Restore the existing client through its tray activation path."""
        self.tray.open_client()
        time.sleep(0.5)

    def open_chat(self, friend_name: str) -> None:
        """Search a contact and open the first matching chat result."""
        friend_name = self._require_text(friend_name, "friend_name")
        self.open()
        window = self._main_window()
        window.set_focus()
        window.type_keys("^f")
        time.sleep(0.25)
        window.type_keys(friend_name, with_spaces=True, vk_packet=True)
        time.sleep(0.35)
        window.type_keys("{ENTER}")
        time.sleep(0.4)

    def send_message(self, friend_name: str, message: str) -> None:
        """Send one plain-text message to the first matching search result."""
        message = self._require_text(message, "message")
        self.open_chat(friend_name)
        window = self._main_window()
        window.set_focus()
        window.type_keys(message, with_spaces=True, vk_packet=True)
        window.type_keys("{ENTER}")

    def send_file(self, friend_name: str, file_name: str | Path) -> None:
        """Send one existing local file to the first matching search result."""
        file_path = Path(file_name).expanduser().resolve()
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.open_chat(friend_name)
        self.clipboard.copy_file(file_path)
        window = self._main_window()
        window.set_focus()
        window.type_keys("^v")
        time.sleep(0.6)
        window.type_keys("{ENTER}")

    def _main_window(self):
        window = self.desktop.window(
            title=WECHAT_WINDOW_TITLE,
            class_name=WECHAT_WINDOW_CLASS,
        )
        try:
            window.wait("visible ready", timeout=self.timeout)
        except Exception as error:
            raise WeChatWindowNotFoundError(
                "WeChat's main window is not visible after tray activation."
            ) from error
        return window

    @staticmethod
    def _require_text(value: str, field_name: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError(f"{field_name} cannot be empty")
        return value
