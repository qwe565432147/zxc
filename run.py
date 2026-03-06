"""
启动脚本
========

这是程序的独立启动脚本，可以直接运行此文件启动程序。

使用方法：
    python run.py

或者使用poetry：
    poetry run python run.py
"""

import sys
from pathlib import Path

# 将项目根目录添加到Python路径
# 这样可以确保模块导入正常工作
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from auto_launcher.main import main


if __name__ == "__main__":
    sys.exit(main())
