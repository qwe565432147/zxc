"""
一键打包脚本
============

使用 PyInstaller 将程序打包成 exe 文件。
打包结果放在 build 文件夹中。
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build():
    """清理旧的打包文件"""
    dirs_to_clean = ["build", "dist", "__pycache__"]
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name, ignore_errors=True)
    
    spec_file = "auto_launcher.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)
        print(f"清理文件: {spec_file}")


def build_exe():
    """执行打包"""
    print("\n" + "=" * 50)
    print("开始打包...")
    print("=" * 50 + "\n")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=AutoLauncher",
        "--windowed",
        "--onefile",
        "--clean",
        "--noconfirm",
        "--add-data=auto_launcher/resources;auto_launcher/resources",
        "--hidden-import=PySide6",
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        "--hidden-import=PIL",
        "run.py"
    ]
    
    result = subprocess.run(cmd, cwd=os.getcwd())
    
    if result.returncode != 0:
        print("\n打包失败!")
        return False
    
    return True


def organize_output():
    """整理输出文件"""
    print("\n" + "=" * 50)
    print("整理输出文件...")
    print("=" * 50 + "\n")
    
    build_dir = Path("build")
    build_dir.mkdir(exist_ok=True)
    
    dist_exe = Path("dist/AutoLauncher.exe")
    if dist_exe.exists():
        target = build_dir / "AutoLauncher.exe"
        shutil.copy2(dist_exe, target)
        print(f"已复制: {target}")
        print(f"文件大小: {target.stat().st_size / 1024 / 1024:.2f} MB")
        return True
    else:
        print("未找到生成的exe文件!")
        return False


def main():
    print("\n" + "=" * 50)
    print("AutoLauncher 一键打包工具")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    os.chdir(project_root)
    print(f"工作目录: {os.getcwd()}")
    
    clean_build()
    
    if build_exe():
        if organize_output():
            print("\n" + "=" * 50)
            print("打包完成!")
            print(f"输出位置: {Path('build/AutoLauncher.exe').absolute()}")
            print("=" * 50 + "\n")
        else:
            print("\n打包过程中出现问题")
            sys.exit(1)
    else:
        print("\n打包失败!")
        sys.exit(1)


if __name__ == "__main__":
    main()
