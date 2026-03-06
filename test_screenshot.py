"""测试截图向导"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from auto_launcher.utils.screenshot_tool import TemplateCaptureWizard
    print("导入 TemplateCaptureWizard 成功")
except Exception as e:
    print(f"导入失败: {e}")
    import traceback
    traceback.print_exc()
