"""
测试改进后的图像识别模块
========================

这个脚本用于测试图像识别的各种匹配方法效果。
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from auto_launcher.utils.image_recognition import ImageRecognizer
from auto_launcher.utils.runtime import TEMPLATES_DIR


def test_template_match(recognizer: ImageRecognizer, template_name: str):
    """测试单个模板的匹配"""
    print(f"\n{'='*60}")
    print(f"测试模板: {template_name}")
    print(f"{'='*60}")
    
    # 获取模板信息
    info = recognizer.get_template_info(template_name)
    if info:
        print(f"模板信息: {info['width']}x{info['height']}, 路径: {info['path']}")
    else:
        print(f"错误: 模板 '{template_name}' 不存在")
        return
    
    # 运行测试
    result = recognizer.test_match(template_name)
    
    print(f"\n截图尺寸: {result.get('screenshot_size', 'N/A')}")
    print(f"阈值: {result.get('threshold', 'N/A')}")
    print(f"\n各方法匹配结果:")
    print("-" * 40)
    
    methods = result.get("methods", {})
    
    for method_name, method_result in methods.items():
        found = "✓ 找到" if method_result.get("found") else "✗ 未找到"
        confidence = method_result.get("confidence", 0)
        position = method_result.get("position")
        scale = method_result.get("scale", "")
        
        pos_str = f"位置: {position}" if position else ""
        scale_str = f"缩放: {scale}" if scale else ""
        
        print(f"  [{method_name:12}] {found} | 置信度: {confidence:.4f} {pos_str} {scale_str}")
    
    # 总结
    print("-" * 40)
    best_method = None
    best_confidence = 0
    
    for method_name, method_result in methods.items():
        if method_result.get("found") and method_result.get("confidence", 0) > best_confidence:
            best_confidence = method_result["confidence"]
            best_method = method_name
    
    if best_method:
        print(f"推荐使用: {best_method} (置信度: {best_confidence:.4f})")
    else:
        print("警告: 所有方法都未能匹配成功!")
        max_conf = max(m.get("confidence", 0) for m in methods.values())
        print(f"最高置信度: {max_conf:.4f} (需要 >= 0.8)")


def main():
    print("=" * 60)
    print("图像识别测试工具")
    print("=" * 60)
    print(f"模板目录: {TEMPLATES_DIR}")
    
    # 列出可用的模板
    templates = list(TEMPLATES_DIR.glob("*.png"))
    if templates:
        print(f"\n可用模板 ({len(templates)} 个):")
        for t in templates:
            print(f"  - {t.stem}")
    else:
        print("\n警告: 没有找到任何模板文件!")
        return
    
    # 创建识别器
    recognizer = ImageRecognizer(TEMPLATES_DIR)
    
    # 开启调试模式
    debug_dir = project_root / "logs" / "debug"
    recognizer.set_debug_mode(True, debug_dir)
    print(f"\n调试模式已开启，图像将保存到: {debug_dir}")
    
    # 测试所有模板
    while True:
        print("\n" + "=" * 60)
        print("选项:")
        print("  1. 测试所有模板")
        print("  2. 测试指定模板")
        print("  3. 退出")
        print("=" * 60)
        
        choice = input("请选择 (1/2/3): ").strip()
        
        if choice == "1":
            for template_file in templates:
                test_template_match(recognizer, template_file.stem)
                
        elif choice == "2":
            name = input("请输入模板名称 (不含.png): ").strip()
            if name:
                test_template_match(recognizer, name)
            else:
                print("错误: 模板名称不能为空")
                
        elif choice == "3":
            print("退出测试")
            break
        else:
            print("无效选择，请重新输入")


if __name__ == "__main__":
    main()