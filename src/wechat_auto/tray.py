"""Notification-area discovery for the signed-in WeChat client."""

from __future__ import annotations

from typing import Any

from pywinauto import Desktop

from wechat_auto.constants import (
    HIDDEN_ICONS_BUTTON_TITLE,
    OVERFLOW_WINDOW_CLASS,
    TRAY_WINDOW_CLASS,
    WECHAT_TRAY_NAME,
)
from wechat_auto.exceptions import TrayIconNotFoundError


class WeChatTray:
    """Find and activate WeChat through its real notification-area control."""

    def __init__(self, desktop: Desktop, timeout: float = 5) -> None:
        self.desktop = desktop
        self.timeout = timeout

    def open_client(self) -> None:
        """Double-click the exact WeChat tray icon to restore its own UI state."""
        icon = self._find_in_main_tray() or self._find_in_overflow()
        if icon is None:
            raise TrayIconNotFoundError(
                "WeChat tray icon was not found. Ensure WeChat is running and signed in."
            )
        icon.double_click_input()

    def _find_in_main_tray(self) -> Any | None:
        tray = self.desktop.window(class_name=TRAY_WINDOW_CLASS)
        tray.wait("exists ready", timeout=self.timeout)
        return self._find_exact_icon(tray)

    def _find_in_overflow(self) -> Any | None:
        tray = self.desktop.window(class_name=TRAY_WINDOW_CLASS)
        hidden_icons = tray.child_window(
            title=HIDDEN_ICONS_BUTTON_TITLE,
            control_type="Button",
        )
        try:
            hidden_icons.click_input()
            overflow = self.desktop.window(class_name=OVERFLOW_WINDOW_CLASS)
            overflow.wait("visible ready", timeout=self.timeout)
        except Exception:  # The overflow panel may not exist on a given taskbar.
            return None
        return self._find_exact_icon(overflow)

    @staticmethod
    def _find_exact_icon(container: Any) -> Any | None:
        for button in container.descendants(control_type="Button"):
            if (button.window_text() or "").strip() == WECHAT_TRAY_NAME:
                return button
        return None
