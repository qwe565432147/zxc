"""
程序入口模块
============

这是程序的启动入口，负责：
1. 初始化Qt应用程序
2. 创建并显示主窗口
3. 启动事件循环

对于新手来说，理解这个模块需要知道：
1. QApplication是Qt应用程序的核心类
2. 每个Qt程序只能有一个QApplication实例
3. exec()启动事件循环，程序在这里等待用户操作
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from .ui.main_window import MainWindow


def main():
    """
    程序主入口函数
    
    这是程序启动时调用的第一个函数。
    它完成了以下工作：
    1. 创建QApplication实例
    2. 创建主窗口
    3. 显示窗口
    4. 启动事件循环
    
    返回：
        程序退出码（0表示正常退出）
    """
    # ========== 创建应用程序实例 ==========
    # QApplication管理整个应用程序的控制流和主要设置
    # sys.argv包含命令行参数，Qt会处理一些特定的参数
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("自动化脚本启动器")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("Your Organization")
    
    # ========== 设置高DPI支持 ==========
    # 在高分辨率屏幕上，需要启用高DPI缩放
    # 这行代码让Qt自动处理高DPI显示
    # 注意：PySide6默认已启用，这里只是确保
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # ========== 创建并显示主窗口 ==========
    window = MainWindow()
    
    # 显示窗口
    # show()方法让窗口变为可见
    window.show()
    
    # ========== 启动事件循环 ==========
    # exec()启动Qt的事件循环
    # 程序会在这里等待，直到窗口被关闭
    # 返回值是退出码，通常0表示正常退出
    exit_code = app.exec()
    
    return exit_code


# ========== Python模块入口点 ==========
# 当直接运行这个模块时（python -m auto_launcher.main），
# __name__会是"__main__"，此时执行main()函数
if __name__ == "__main__":
    sys.exit(main())
