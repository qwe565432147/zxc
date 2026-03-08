"""
运行时环境工具模块
==================

处理程序在不同运行环境下的路径问题：
- 作为脚本运行：使用项目目录
- 作为exe运行：使用exe所在目录下的auto_temp文件夹
"""

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """判断是否为打包后的exe运行"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_runtime_dir() -> Path:
    """
    获取运行时目录
    
    - exe运行：exe所在目录/auto_temp
    - 脚本运行：项目根目录
    """
    if is_frozen():
        exe_dir = Path(sys.executable).parent
        runtime_dir = exe_dir / "auto_temp"
    else:
        runtime_dir = Path(__file__).parent.parent.parent
    
    runtime_dir.mkdir(parents=True, exist_ok=True)
    return runtime_dir


def get_templates_dir() -> Path:
    """获取模板图片目录"""
    runtime_dir = get_runtime_dir()
    templates_dir = runtime_dir / "templates"
    templates_dir.mkdir(parents=True, exist_ok=True)
    return templates_dir


def get_logs_dir() -> Path:
    """获取日志目录"""
    runtime_dir = get_runtime_dir()
    logs_dir = runtime_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def get_config_dir() -> Path:
    """获取配置目录"""
    runtime_dir = get_runtime_dir()
    config_dir = runtime_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    """获取数据目录"""
    runtime_dir = get_runtime_dir()
    data_dir = runtime_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


RUNTIME_DIR = get_runtime_dir()
TEMPLATES_DIR = get_templates_dir()
LOGS_DIR = get_logs_dir()
CONFIG_DIR = get_config_dir()
DATA_DIR = get_data_dir()
