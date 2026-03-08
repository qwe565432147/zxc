"""测试模板匹配"""
from auto_launcher.utils.image_recognition import ImageRecognizer

recognizer = ImageRecognizer()

print("=" * 50)
print("检查模板文件")
print("=" * 50)

for name in ['rdp_connected', 'rdp_disconnected', 'rdp_sleeping', 'rdp_reconnect_button']:
    template = recognizer.load_template(name)
    if template is not None:
        print(f'{name}: 尺寸 {template.shape}')
    else:
        print(f'{name}: 加载失败')

print()
print("=" * 50)
print("测试屏幕匹配 (阈值0.7)")
print("=" * 50)

for name in ['rdp_connected', 'rdp_disconnected', 'rdp_sleeping']:
    result = recognizer.find_template_by_name(name, threshold=0.7)
    status = "找到" if result.found else "未找到"
    print(f'{name}: {status}, 置信度={result.confidence:.3f}')

print()
print("=" * 50)
print("检测RDP状态")
print("=" * 50)
status = recognizer.check_rdp_status()
print(f"RDP状态: {status}")
