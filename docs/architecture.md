# Architecture

`wechat_auto` uses a layered design so desktop-specific code is isolated and future features can be added safely.

```text
CLI / console script
        |
   WeChatClient            High-level workflows: open, search, send text/file
     |       |
  WeChatTray  FileClipboard Platform adapters: UIA tray and CF_HDROP clipboard
```

## Design decisions

- **Tray activation instead of `ShowWindow`:** the WeChat Qt client must process its own tray activation to restore its rendered content. Forcing a hidden window visible can yield a white shell.
- **Native search shortcut:** WeChat 4.x exposes only its root Qt pane through UI Automation. The validated `Ctrl+F` path is more stable than fixed screen coordinates.
- **Isolated Windows APIs:** all 64-bit handle declarations live in `clipboard.py`, where they can be tested independently.
- **Side-effect boundaries:** `send_message` and `send_file` are explicit operations. Keep recipient/result verification close to those calls when extending the project.

## Extension guide

For a new interaction, first capture baseline state, manually perform the action once, capture again, and automate the real entry point indicated by the delta. See the repository's desktop automation skill for the full workflow.
