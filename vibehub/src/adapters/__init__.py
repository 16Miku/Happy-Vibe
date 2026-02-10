"""数据适配器模块。

提供各种编码工具的日志解析和数据采集功能。
"""

from src.adapters.base import BaseAdapter, ActivityData
from src.adapters.claude_code import ClaudeCodeAdapter

__all__ = ["BaseAdapter", "ActivityData", "ClaudeCodeAdapter"]
