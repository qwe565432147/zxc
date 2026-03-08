"""
模板图像资源目录
================

这个目录用于存放图像识别所需的模板图像。

模板图像命名规范：
-----------------
- rdp_connected.png    : RDP已连接状态的识别特征
- rdp_disconnected.png : RDP断开连接状态的识别特征
- rdp_sleeping.png     : 远程电脑休眠状态的识别特征
- rdp_reconnect_button.png : RDP重连按钮
- rdp_session_icon.png : RDP会话图标
- automation_script.png : 自动化脚本图标

如何创建模板图像：
-----------------
1. 运行程序，点击"测试"按钮进入模板创建模式
2. 或者使用以下Python代码手动创建：

    from auto_launcher.utils.image_recognition import ImageRecognizer
    
    recognizer = ImageRecognizer()
    
    # 截取屏幕区域作为模板
    # region = (x, y, width, height)
    recognizer.capture_and_save_template("rdp_connected", (100, 100, 200, 50))

模板图像要求：
-------------
- 格式：PNG（支持透明度）
- 尺寸：尽量小，但要包含足够的特征
- 内容：清晰、无模糊、对比度高
- 注意：模板必须与实际屏幕显示一致（包括缩放比例）

常见问题：
---------
1. 识别失败：检查模板是否与实际显示一致
2. 误识别：提高匹配阈值（默认0.8）
3. 识别慢：减小模板尺寸
"""
