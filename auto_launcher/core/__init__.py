"""
核心功能模块
============

包含程序的核心业务逻辑：
- countdown: 倒计时管理
- automation: 自动化操作执行器
"""

from .countdown import CountdownManager
from .automation import AutomationExecutor

__all__ = ["CountdownManager", "AutomationExecutor"]
