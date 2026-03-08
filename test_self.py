"""
自验证脚本
==========

用于验证项目各模块是否正常工作。
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试所有模块是否能正常导入"""
    print("=" * 50)
    print("测试模块导入...")
    print("=" * 50)
    
    errors = []
    
    # 测试核心模块
    try:
        from auto_launcher.core.countdown import CountdownManager
        print("[OK] CountdownManager 导入成功")
    except Exception as e:
        errors.append(f"CountdownManager: {e}")
        print(f"[FAIL] CountdownManager: {e}")
    
    try:
        from auto_launcher.core.automation import AutomationExecutor, ExecutionConfig
        print("[OK] AutomationExecutor 导入成功")
    except Exception as e:
        errors.append(f"AutomationExecutor: {e}")
        print(f"[FAIL] AutomationExecutor: {e}")
    
    # 测试工具模块
    try:
        from auto_launcher.utils.image_recognition import ImageRecognizer
        print("[OK] ImageRecognizer 导入成功")
    except Exception as e:
        errors.append(f"ImageRecognizer: {e}")
        print(f"[FAIL] ImageRecognizer: {e}")
    
    try:
        from auto_launcher.utils.system_utils import SystemController
        print("[OK] SystemController 导入成功")
    except Exception as e:
        errors.append(f"SystemController: {e}")
        print(f"[FAIL] SystemController: {e}")
    
    # 测试UI模块
    try:
        from auto_launcher.ui.main_window import MainWindow
        print("[OK] MainWindow 导入成功")
    except Exception as e:
        errors.append(f"MainWindow: {e}")
        print(f"[FAIL] MainWindow: {e}")
    
    # 测试主入口
    try:
        from auto_launcher.main import main
        print("[OK] main 函数导入成功")
    except Exception as e:
        errors.append(f"main: {e}")
        print(f"[FAIL] main: {e}")
    
    return errors


def test_countdown():
    """测试倒计时功能"""
    print("\n" + "=" * 50)
    print("测试倒计时功能...")
    print("=" * 50)
    
    try:
        from auto_launcher.core.countdown import CountdownManager
        
        # 创建倒计时管理器
        cm = CountdownManager()
        
        # 测试设置时间
        cm.set_countdown(1, 30, 45)  # 1小时30分45秒
        expected_seconds = 1 * 3600 + 30 * 60 + 45
        
        if cm.remaining_seconds == expected_seconds:
            print(f"[OK] 倒计时设置正确: {cm.remaining_seconds}秒")
        else:
            print(f"[FAIL] 倒计时设置错误: 期望{expected_seconds}, 实际{cm.remaining_seconds}")
            return False
        
        # 测试格式化
        formatted = CountdownManager.format_time(5445)  # 1小时30分45秒
        if formatted == "01:30:45":
            print(f"[OK] 时间格式化正确: {formatted}")
        else:
            print(f"[FAIL] 时间格式化错误: {formatted}")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 倒计时测试失败: {e}")
        return False


def test_image_recognizer():
    """测试图像识别器"""
    print("\n" + "=" * 50)
    print("测试图像识别器...")
    print("=" * 50)
    
    try:
        from auto_launcher.utils.image_recognition import ImageRecognizer
        
        recognizer = ImageRecognizer()
        
        # 检查模板目录
        print(f"[OK] 模板目录: {recognizer.templates_dir}")
        
        # 测试截图功能
        screenshot = recognizer._take_screenshot()
        if screenshot is not None:
            print(f"[OK] 截图功能正常, 尺寸: {screenshot.shape}")
        else:
            print("[FAIL] 截图功能失败")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 图像识别器测试失败: {e}")
        return False


def test_system_controller():
    """测试系统控制器"""
    print("\n" + "=" * 50)
    print("测试系统控制器...")
    print("=" * 50)
    
    try:
        from auto_launcher.utils.system_utils import SystemController
        
        controller = SystemController()
        
        # 测试获取屏幕尺寸
        width, height = controller.get_screen_size()
        print(f"[OK] 屏幕尺寸: {width}x{height}")
        
        # 测试获取鼠标位置
        x, y = controller.get_mouse_position()
        print(f"[OK] 鼠标位置: ({x}, {y})")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 系统控制器测试失败: {e}")
        return False


def test_automation_config():
    """测试自动化配置"""
    print("\n" + "=" * 50)
    print("测试自动化配置...")
    print("=" * 50)
    
    try:
        from auto_launcher.core.automation import ExecutionConfig, ExecutionState
        
        # 测试配置创建
        config = ExecutionConfig(
            target_program_path=r"D:\ProgramData\Quark\auto.exe",
            rdp_reconnect_attempts=5
        )
        
        print(f"[OK] 配置创建成功")
        print(f"    - 目标程序: {config.target_program_path}")
        print(f"    - 重连次数: {config.rdp_reconnect_attempts}")
        
        # 测试状态枚举
        print(f"[OK] 执行状态枚举: {[s.name for s in ExecutionState]}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 自动化配置测试失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n")
    print("*" * 50)
    print("*  自动化脚本启动器 - 自验证程序")
    print("*" * 50)
    print()
    
    all_passed = True
    
    # 运行测试
    import_errors = test_imports()
    if import_errors:
        all_passed = False
        print(f"\n导入错误: {len(import_errors)}个")
        for err in import_errors:
            print(f"  - {err}")
    
    if not test_countdown():
        all_passed = False
    
    if not test_image_recognizer():
        all_passed = False
    
    if not test_system_controller():
        all_passed = False
    
    if not test_automation_config():
        all_passed = False
    
    # 总结
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ 所有测试通过！程序可以正常运行。")
    else:
        print("✗ 部分测试失败，请检查错误信息。")
    print("=" * 50)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
