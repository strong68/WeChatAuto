"""Domain errors exposed by WeChatAuto."""


class WeChatAutoError(RuntimeError):
    """Base error for automation failures."""


class TrayIconNotFoundError(WeChatAutoError):
    """Raised when WeChat is not available in the notification area."""


class WeChatWindowNotFoundError(WeChatAutoError):
    """Raised when WeChat's rendered main window is not available."""


class AmbiguousRecipientError(WeChatAutoError):
    """Reserved for future result verification with duplicate contacts."""
