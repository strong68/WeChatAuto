"""Command-line interface for WeChatAuto."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Sequence

from pywinauto.findwindows import ElementNotFoundError

from wechat_auto.client import WeChatClient
from wechat_auto.exceptions import WeChatAutoError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Operate an already-signed-in Windows WeChat client."
    )
    parser.add_argument("friend", nargs="?", help="Unique contact remark/name to search")
    parser.add_argument("--send", metavar="MESSAGE", help="Send one plain-text message")
    parser.add_argument("--file", metavar="PATH", help="Send one existing local file")
    parser.add_argument("--verbose", action="store_true", help="Enable diagnostic logging")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.send is not None and args.file is not None:
        parser.error("use either --send or --file, not both")
    if (args.send is not None or args.file is not None) and not args.friend:
        parser.error("friend is required when using --send or --file")

    client = WeChatClient()
    try:
        if args.file is not None:
            client.send_file(args.friend, args.file)
            print(f"Sent file to: {args.friend}")
        elif args.send is not None:
            client.send_message(args.friend, args.send)
            print(f"Sent message to: {args.friend}")
        elif args.friend:
            client.open_chat(args.friend)
            print(f"Opened WeChat search result for: {args.friend}")
        else:
            client.open()
            print("Activated the existing WeChat tray icon.")
    except (ElementNotFoundError, TimeoutError, WeChatAutoError, OSError) as error:
        parser.exit(1, f"error: {error}\n")
    return 0
