# WeChatAuto

Windows 微信桌面端自动化示例：唤起已登录微信、搜索并打开聊天、发送文本和发送文件。

> 仅用于你有权操作的微信账号和联系人。发送消息或文件前，请确认收件人和内容无误。

## 环境

- Windows 10/11
- 已登录并运行中的微信 Windows 客户端
- Conda 环境：`WeChatAuto`
- Python 依赖：`pywinauto`、`pywin32`

## 安装

```powershell
conda activate WeChatAuto
pip install pywinauto pywin32
```

## 使用

### 唤起已登录微信

```powershell
python main.py
```

程序通过系统托盘中名称精确为“微信”的图标双击唤起客户端，不会重新启动 `Weixin.exe`，避免出现新实例或空白窗口。

### 搜索并打开聊天

```powershell
python main.py 好友备注名
```

微信会搜索该名称并打开首个结果。请尽量使用唯一的好友备注名。

### 发送文本消息

```powershell
python main.py 好友备注名 --send "你好，这是一条测试消息"
```

### 发送文件

```powershell
python main.py 好友备注名 --file "D:\\path\\to\\report.pdf"
```

文件会通过 Windows `CF_HDROP` 文件剪贴板粘贴到聊天窗口后发送。

## 实现说明

微信 4.x 的 Qt 窗口不完整暴露 UI Automation 控件。直接调用 Windows `ShowWindow` 虽能显示窗口外壳，但可能跳过微信的内部恢复事件并出现白屏。本项目改为复现人工操作路径：通过任务栏通知区域的微信托盘图标唤起，再使用微信原生 `Ctrl+F` 搜索快捷键。

## 限制

- 同名联系人会打开搜索结果中的第一位；请使用唯一备注名。
- 该项目依赖中文系统托盘控件名称“微信”。若客户端或系统语言不同，需要调整 `WECHAT_TRAY_NAME`。
- 自动化发送属于外部副作用，建议先用测试联系人验证。

## License

MIT
