"""
用户界面模块
============

包含所有GUI相关的代码，使用PySide6实现。
主要组件：
- MainWindow: 主窗口
- CountdownWidget: 倒计时显示组件
- StatusPanel: 状态面板
"""

from .main_window import MainWindow

__all__ = ["MainWindow"]
