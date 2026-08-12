from pathlib import Path

from wechat_auto.clipboard import FileClipboard


def test_build_dropfiles_payload_contains_utf16_path() -> None:
    file_path = Path(r"D:\reports\daily report.pdf")

    payload = FileClipboard.build_dropfiles_payload(file_path)

    assert payload[:20] == b"\x14\x00\x00\x00" + b"\x00" * 12 + b"\x01\x00\x00\x00"
    assert str(file_path).encode("utf-16-le") in payload
    assert payload.endswith(b"\0\0\0\0")
