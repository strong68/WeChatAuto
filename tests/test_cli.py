from unittest.mock import Mock

from wechat_auto import cli


def test_cli_opens_client_without_arguments(monkeypatch) -> None:
    client = Mock()
    monkeypatch.setattr(cli, "WeChatClient", lambda: client)

    result = cli.main([])

    assert result == 0
    client.open.assert_called_once_with()


def test_cli_rejects_multiple_send_modes() -> None:
    try:
        cli.main(["Alice", "--send", "hello", "--file", "report.pdf"])
    except SystemExit as error:
        assert error.code == 2
    else:
        raise AssertionError("expected argument validation to terminate")
