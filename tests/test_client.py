from pathlib import Path
from unittest.mock import Mock

import pytest

from wechat_auto.client import WeChatClient


@pytest.fixture
def client() -> WeChatClient:
    desktop = Mock()
    clipboard = Mock()
    return WeChatClient(desktop=desktop, clipboard=clipboard, timeout=1)


def test_open_chat_uses_native_search_shortcut(
    client: WeChatClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    window = Mock()
    client.tray.open_client = Mock()
    client.desktop.window.return_value = window
    monkeypatch.setattr("wechat_auto.client.time.sleep", lambda _: None)

    client.open_chat(" Alice ")

    assert window.type_keys.call_args_list[0].args == ("^f",)
    assert window.type_keys.call_args_list[1].args == ("Alice",)
    assert window.type_keys.call_args_list[2].args == ("{ENTER}",)


def test_send_file_rejects_missing_path(client: WeChatClient) -> None:
    with pytest.raises(FileNotFoundError):
        client.send_file("Alice", Path("missing.txt"))
