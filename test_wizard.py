"""测试模板配置向导导入"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from auto_launcher.utils.screenshot_tool import TemplateCaptureWizard
    print("导入 TemplateCaptureWizard 成功")
    
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    wizard = TemplateCaptureWizard()
    print("创建向导实例成功")
    wizard.show()
    print("显示向导成功")
    sys.exit(app.exec())
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
