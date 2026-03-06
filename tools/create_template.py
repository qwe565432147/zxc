"""
模板创建工具
============

这个工具帮助你创建图像识别所需的模板图像。

使用方法：
---------
1. 运行此脚本：python tools/create_template.py
2. 按照提示操作
3. 模板会自动保存到resources/templates目录
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pyautogui
import time
from PIL import Image
import cv2
import numpy as np


def create_template_interactive():
    """
    交互式创建模板
    
    这个函数会引导用户完成模板创建过程。
    """
    print("=" * 50)
    print("模板创建工具")
    print("=" * 50)
    print()
    
    # 获取模板名称
    print("可用的模板名称建议：")
    print("  - rdp_connected      : RDP已连接状态")
    print("  - rdp_disconnected   : RDP断开状态")
    print("  - rdp_sleeping       : 远程电脑休眠状态")
    print("  - rdp_reconnect_button : 重连按钮")
    print("  - rdp_session_icon   : RDP会话图标")
    print("  - automation_script  : 自动化脚本图标")
    print()
    
    template_name = input("请输入模板名称: ").strip()
    if not template_name:
        print("错误：模板名称不能为空")
        return
    
    print()
    print("接下来你需要截取屏幕区域作为模板。")
    print("请按照以下步骤操作：")
    print()
    print("1. 准备好要截取的屏幕区域")
    print("2. 记下区域的左上角坐标 (x, y)")
    print("3. 记下区域的宽度和高度 (width, height)")
    print()
    
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    print(f"当前屏幕尺寸: {screen_width} x {screen_height}")
    print()
    
    # 获取区域信息
    try:
        x = int(input("请输入左上角X坐标: "))
        y = int(input("请输入左上角Y坐标: "))
        width = int(input("请输入宽度: "))
        height = int(input("请输入高度: "))
    except ValueError:
        print("错误：请输入有效的数字")
        return
    
    # 验证区域
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        print("错误：区域参数无效")
        return
    
    if x + width > screen_width or y + height > screen_height:
        print("错误：区域超出屏幕范围")
        return
    
    print()
    print(f"将截取区域: ({x}, {y}) 到 ({x + width}, {y + height})")
    
    # 倒计时
    print()
    print("将在3秒后开始截取...")
    for i in range(3, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    
    # 截取屏幕
    print()
    print("正在截取...")
    
    try:
        # 使用pyautogui截图
        screenshot = pyautogui.screenshot(region=(x, y, width, height))
        
        # 转换为OpenCV格式
        opencv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        
        # 保存模板
        templates_dir = project_root / "auto_launcher" / "resources" / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        template_path = templates_dir / f"{template_name}.png"
        cv2.imwrite(str(template_path), opencv_image)
        
        print(f"模板已保存: {template_path}")
        
        # 显示预览
        print()
        print("模板预览（按任意键关闭）：")
        cv2.imshow("Template Preview", opencv_image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        print()
        print("模板创建完成！")
        
    except Exception as e:
        print(f"错误：{e}")


def list_templates():
    """
    列出所有已存在的模板
    """
    templates_dir = project_root / "auto_launcher" / "resources" / "templates"
    
    print()
    print("已存在的模板：")
    print("-" * 30)
    
    if not templates_dir.exists():
        print("  (无)")
        return
    
    templates = list(templates_dir.glob("*.png"))
    if not templates:
        print("  (无)")
        return
    
    for template in templates:
        # 读取图像尺寸
        img = cv2.imread(str(template))
        if img is not None:
            h, w = img.shape[:2]
            print(f"  {template.stem}: {w}x{h}")


def main():
    """
    主函数
    """
    while True:
        print()
        print("=" * 50)
        print("模板管理工具")
        print("=" * 50)
        print()
        print("1. 创建新模板")
        print("2. 列出所有模板")
        print("3. 退出")
        print()
        
        choice = input("请选择操作 (1-3): ").strip()
        
        if choice == "1":
            create_template_interactive()
        elif choice == "2":
            list_templates()
        elif choice == "3":
            print("再见！")
            break
        else:
            print("无效的选择，请重新输入")


if __name__ == "__main__":
    main()
