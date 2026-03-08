"""
图像识别模块
============

这个模块使用OpenCV实现图像识别功能，主要用于：
1. 识别RDP连接状态（已连接/断连/休眠待登录）
2. 识别桌面上的文件夹和脚本图标
3. 定位需要点击的UI元素

改进版本特性：
- 多尺度匹配：支持不同缩放级别的模板匹配
- 边缘匹配：使用Canny边缘检测，对颜色变化更鲁棒
- 灰度匹配：减少颜色干扰
- 调试模式：生成匹配结果可视化图像
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List, Callable
from dataclasses import dataclass
import mss
import time

from .runtime import TEMPLATES_DIR


@dataclass
class MatchResult:
    """
    匹配结果数据类
    
    属性：
        found: 是否找到匹配
        position: 匹配位置的中心点坐标 (x, y)
        confidence: 匹配置信度 (0-1之间，越大越匹配)
        rectangle: 匹配区域的矩形 (x, y, width, height)
        method: 匹配使用的方法（用于调试）
        scale: 匹配时的缩放比例
    """
    found: bool
    position: Optional[Tuple[int, int]] = None
    confidence: float = 0.0
    rectangle: Optional[Tuple[int, int, int, int]] = None
    method: str = ""
    scale: float = 1.0


class ImageRecognizer:
    """
    图像识别器类 - 增强版
    
    改进功能：
    - 多尺度匹配：自动尝试不同缩放级别
    - 边缘匹配：使用Canny边缘，对颜色变化更鲁棒
    - 灰度匹配：减少颜色干扰
    - 调试模式：保存匹配过程图像
    - 智能阈值：自动调整匹配阈值
    """
    
    DEFAULT_THRESHOLD = 0.8
    MULTI_SCALE_THRESHOLD = 0.75  # 多尺度匹配使用稍低的阈值
    EDGE_THRESHOLD = 0.7  # 边缘匹配阈值
    
    RDP_CONNECTED = "connected"
    RDP_DISCONNECTED = "disconnected"
    RDP_SLEEPING = "sleeping"
    RDP_UNKNOWN = "unknown"
    
    def __init__(self, templates_dir: Optional[Path] = None):
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = TEMPLATES_DIR
        
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
        self._template_cache: dict = {}
        self._window_capture_func = None
        
        # 调试模式设置
        self._debug_mode = False
        self._debug_dir = None
        
        # 多尺度匹配参数
        self._scale_range = (0.7, 1.3)  # 缩放范围
        self._scale_steps = 13  # 缩放步数
    
    def set_window_capture(self, capture_func: Callable) -> None:
        """设置窗口截图函数"""
        self._window_capture_func = capture_func
    
    def set_debug_mode(self, enabled: bool, debug_dir: Optional[Path] = None) -> None:
        """
        设置调试模式
        
        参数：
            enabled: 是否启用
            debug_dir: 调试图像保存目录
        """
        self._debug_mode = enabled
        if debug_dir:
            self._debug_dir = Path(debug_dir)
            self._debug_dir.mkdir(parents=True, exist_ok=True)
    
    def set_scale_params(self, min_scale: float, max_scale: float, steps: int) -> None:
        """设置多尺度匹配参数"""
        self._scale_range = (min_scale, max_scale)
        self._scale_steps = steps
    
    # ========== 模板管理方法 ==========
    
    def load_template(self, name: str) -> Optional[np.ndarray]:
        """加载模板图像"""
        if name in self._template_cache:
            return self._template_cache[name]
        
        template_path = self.templates_dir / f"{name}.png"
        
        if not template_path.exists():
            print(f"[图像识别] 模板文件不存在: {template_path}")
            return None
        
        template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
        
        if template is None:
            print(f"[图像识别] 无法读取模板图像: {template_path}")
            return None
        
        self._template_cache[name] = template
        print(f"[图像识别] 已加载模板: {name}, 尺寸: {template.shape[:2]}")
        return template
    
    def save_template(self, name: str, image: np.ndarray) -> bool:
        """保存模板图像"""
        template_path = self.templates_dir / f"{name}.png"
        success = cv2.imwrite(str(template_path), image)
        
        if success:
            self._template_cache[name] = image
            print(f"[图像识别] 模板已保存: {template_path}")
        else:
            print(f"[图像识别] 模板保存失败: {template_path}")
        
        return success
    
    def capture_and_save_template(self, name: str, 
                                   region: Tuple[int, int, int, int]) -> bool:
        """截取屏幕区域并保存为模板"""
        x, y, width, height = region
        with mss.mss() as sct:
            monitor = {'left': x, 'top': y, 'width': width, 'height': height}
            screenshot = sct.grab(monitor)
            opencv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGRA2BGR)
            return self.save_template(name, opencv_image)
    
    # ========== 核心匹配方法 ==========
    
    def find_template(self, template: np.ndarray, 
                      threshold: float = DEFAULT_THRESHOLD,
                      use_multi_scale: bool = True,
                      use_edge_matching: bool = True) -> MatchResult:
        """
        在屏幕或绑定窗口内查找模板（增强版）
        
        匹配策略：
        1. 首先尝试标准彩色模板匹配
        2. 如果失败，尝试多尺度匹配
        3. 如果仍失败，尝试边缘匹配
        
        参数：
            template: 要查找的模板图像
            threshold: 匹配阈值
            use_multi_scale: 是否使用多尺度匹配
            use_edge_matching: 是否使用边缘匹配作为备选
            
        返回：
            MatchResult对象
        """
        screenshot = self._take_screenshot()
        
        if screenshot is None:
            return MatchResult(found=False, method="screenshot_failed")
        
        if self._debug_mode:
            self._save_debug_image("screenshot.png", screenshot)
            self._save_debug_image("template.png", template)
        
        template_height, template_width = template.shape[:2]
        
        # 检查模板是否比截图大
        screen_height, screen_width = screenshot.shape[:2]
        if template_height > screen_height or template_width > screen_width:
            print(f"[图像识别] 模板({template_width}x{template_height})大于截图({screen_width}x{screen_height})")
            return MatchResult(found=False, method="template_too_large")
        
        # 方法1: 标准彩色模板匹配
        result = self._match_template_standard(screenshot, template, threshold)
        if result.found:
            result.method = "standard_color"
            if self._debug_mode:
                print(f"[图像识别] 标准匹配成功，置信度: {result.confidence:.3f}")
            return result
        
        # 方法2: 多尺度匹配
        if use_multi_scale:
            result = self._match_template_multi_scale(screenshot, template, threshold)
            if result.found:
                result.method = "multi_scale"
                if self._debug_mode:
                    print(f"[图像识别] 多尺度匹配成功，置信度: {result.confidence:.3f}, 缩放: {result.scale:.2f}")
                return result
        
        # 方法3: 灰度匹配
        result = self._match_template_grayscale(screenshot, template, threshold * 0.95)
        if result.found:
            result.method = "grayscale"
            if self._debug_mode:
                print(f"[图像识别] 灰度匹配成功，置信度: {result.confidence:.3f}")
            return result
        
        # 方法4: 边缘匹配
        if use_edge_matching:
            result = self._match_template_edge(screenshot, template, self.EDGE_THRESHOLD)
            if result.found:
                result.method = "edge"
                if self._debug_mode:
                    print(f"[图像识别] 边缘匹配成功，置信度: {result.confidence:.3f}")
                return result
        
        if self._debug_mode:
            print(f"[图像识别] 所有匹配方法均失败，最高置信度: {result.confidence:.3f}")
        
        return MatchResult(found=False, confidence=result.confidence, method="all_methods_failed")
    
    def _match_template_standard(self, screenshot: np.ndarray, 
                                  template: np.ndarray,
                                  threshold: float) -> MatchResult:
        """标准模板匹配"""
        try:
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                template_height, template_width = template.shape[:2]
                center_x = max_loc[0] + template_width // 2
                center_y = max_loc[1] + template_height // 2
                
                if self._debug_mode:
                    self._save_match_result(screenshot, max_loc, template_width, template_height, max_val)
                
                return MatchResult(
                    found=True,
                    position=(center_x, center_y),
                    confidence=float(max_val),
                    rectangle=(max_loc[0], max_loc[1], template_width, template_height)
                )
            
            return MatchResult(found=False, confidence=float(max_val))
        except Exception as e:
            print(f"[图像识别] 标准匹配异常: {e}")
            return MatchResult(found=False)
    
    def _match_template_multi_scale(self, screenshot: np.ndarray,
                                     template: np.ndarray,
                                     threshold: float) -> MatchResult:
        """多尺度模板匹配"""
        best_result = MatchResult(found=False, confidence=0.0)
        
        scales = np.linspace(self._scale_range[0], self._scale_range[1], self._scale_steps)
        
        for scale in scales:
            if scale == 1.0:
                continue
            
            # 缩放模板
            resized_template = self._resize_template(template, scale)
            if resized_template is None:
                continue
            
            th, tw = resized_template.shape[:2]
            sh, sw = screenshot.shape[:2]
            
            if th > sh or tw > sw:
                continue
            
            try:
                result = cv2.matchTemplate(screenshot, resized_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_result.confidence:
                    # 将缩放后的位置转换回原始模板的位置
                    original_th, original_tw = template.shape[:2]
                    center_x = int((max_loc[0] + tw // 2))
                    center_y = int((max_loc[1] + th // 2))
                    
                    best_result = MatchResult(
                        found=max_val >= self.MULTI_SCALE_THRESHOLD,
                        position=(center_x, center_y),
                        confidence=float(max_val),
                        rectangle=(max_loc[0], max_loc[1], tw, th),
                        scale=scale
                    )
                    
                    if best_result.found:
                        return best_result
            except Exception:
                continue
        
        return best_result
    
    def _match_template_grayscale(self, screenshot: np.ndarray,
                                   template: np.ndarray,
                                   threshold: float) -> MatchResult:
        """灰度模板匹配"""
        try:
            gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            result = cv2.matchTemplate(gray_screenshot, gray_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                template_height, template_width = template.shape[:2]
                center_x = max_loc[0] + template_width // 2
                center_y = max_loc[1] + template_height // 2
                
                return MatchResult(
                    found=True,
                    position=(center_x, center_y),
                    confidence=float(max_val),
                    rectangle=(max_loc[0], max_loc[1], template_width, template_height)
                )
            
            return MatchResult(found=False, confidence=float(max_val))
        except Exception as e:
            print(f"[图像识别] 灰度匹配异常: {e}")
            return MatchResult(found=False)
    
    def _match_template_edge(self, screenshot: np.ndarray,
                              template: np.ndarray,
                              threshold: float) -> MatchResult:
        """边缘模板匹配"""
        try:
            # 转换为灰度
            gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
            
            # 使用Canny边缘检测
            edge_screenshot = cv2.Canny(gray_screenshot, 50, 150)
            edge_template = cv2.Canny(gray_template, 50, 150)
            
            if self._debug_mode:
                self._save_debug_image("edge_screenshot.png", edge_screenshot)
                self._save_debug_image("edge_template.png", edge_template)
            
            result = cv2.matchTemplate(edge_screenshot, edge_template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                template_height, template_width = template.shape[:2]
                center_x = max_loc[0] + template_width // 2
                center_y = max_loc[1] + template_height // 2
                
                return MatchResult(
                    found=True,
                    position=(center_x, center_y),
                    confidence=float(max_val),
                    rectangle=(max_loc[0], max_loc[1], template_width, template_height)
                )
            
            return MatchResult(found=False, confidence=float(max_val))
        except Exception as e:
            print(f"[图像识别] 边缘匹配异常: {e}")
            return MatchResult(found=False)
    
    def _resize_template(self, template: np.ndarray, scale: float) -> Optional[np.ndarray]:
        """缩放模板"""
        if scale == 1.0:
            return template
        
        height, width = template.shape[:2]
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        if new_width < 10 or new_height < 10:
            return None
        
        interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
        return cv2.resize(template, (new_width, new_height), interpolation=interpolation)
    
    # ========== 便捷方法 ==========
    
    def find_template_by_name(self, name: str, 
                               threshold: float = DEFAULT_THRESHOLD,
                               use_multi_scale: bool = True,
                               use_edge_matching: bool = True) -> MatchResult:
        """
        通过模板名称查找
        
        参数：
            name: 模板名称
            threshold: 匹配阈值
            use_multi_scale: 是否使用多尺度匹配
            use_edge_matching: 是否使用边缘匹配
        """
        template = self.load_template(name)
        if template is None:
            return MatchResult(found=False, method="template_not_found")
        
        return self.find_template(template, threshold, use_multi_scale, use_edge_matching)
    
    def find_all_templates(self, template: np.ndarray,
                           threshold: float = DEFAULT_THRESHOLD) -> List[MatchResult]:
        """查找所有匹配位置"""
        screenshot = self._take_screenshot()
        if screenshot is None:
            return []
        
        template_height, template_width = template.shape[:2]
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        
        locations = np.where(result >= threshold)
        
        results = []
        for pt in zip(*locations[::-1]):
            center_x = pt[0] + template_width // 2
            center_y = pt[1] + template_height // 2
            confidence = result[pt[1], pt[0]]
            
            results.append(MatchResult(
                found=True,
                position=(center_x, center_y),
                confidence=float(confidence),
                rectangle=(pt[0], pt[1], template_width, template_height)
            ))
        
        return results
    
    # ========== RDP状态检测方法 ==========
    
    def check_rdp_status(self) -> str:
        """
        检测RDP连接状态
        
        返回：
            状态字符串：
            - RDP_CONNECTED: 已连接
            - RDP_DISCONNECTED: 已断开
            - RDP_SLEEPING: 远程电脑休眠
            - RDP_UNKNOWN: 无法判断
        """
        # 按优先级检测各种状态
        # 先检测休眠状态（因为休眠时也可能显示断连）
        result = self.find_template_by_name("rdp_sleeping", 0.85)
        if result.found:
            print(f"[图像识别] 检测到休眠状态，置信度: {result.confidence:.3f}")
            return self.RDP_SLEEPING
        
        # 检测断连状态
        result = self.find_template_by_name("rdp_disconnected", 0.85)
        if result.found:
            print(f"[图像识别] 检测到断连状态，置信度: {result.confidence:.3f}")
            return self.RDP_DISCONNECTED
        
        # 检测已连接状态
        result = self.find_template_by_name("rdp_connected", 0.85)
        if result.found:
            print(f"[图像识别] 检测到已连接状态，置信度: {result.confidence:.3f}")
            return self.RDP_CONNECTED
        
        return self.RDP_UNKNOWN
    
    def wait_for_rdp_connection(self, timeout: int = 60,
                                 check_interval: float = 2.0) -> bool:
        """等待RDP连接成功"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.check_rdp_status()
            if status == self.RDP_CONNECTED:
                return True
            
            time.sleep(check_interval)
        
        return False
    
    # ========== 工具方法 ==========
    
    def _take_screenshot(self) -> Optional[np.ndarray]:
        """截取屏幕或绑定窗口并转换为OpenCV格式"""
        try:
            # 优先使用窗口截图函数
            if self._window_capture_func:
                return self._window_capture_func()
            
            # 使用mss进行全屏截图（支持多显示器）
            with mss.mss() as sct:
                # 获取所有显示器的虚拟屏幕
                monitor = sct.monitors[0]  # 0表示所有显示器
                screenshot = sct.grab(monitor)
                # mss返回BGRA格式，转换为BGR
                opencv_image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGRA2BGR)
                return opencv_image
        except Exception as e:
            print(f"[图像识别] 截图失败: {e}")
            return None
    
    def _save_debug_image(self, filename: str, image: np.ndarray) -> None:
        """保存调试图像"""
        if not self._debug_mode or not self._debug_dir:
            return
        
        try:
            filepath = self._debug_dir / filename
            cv2.imwrite(str(filepath), image)
        except Exception as e:
            print(f"[图像识别] 保存调试图像失败: {e}")
    
    def _save_match_result(self, screenshot: np.ndarray, 
                           location: Tuple[int, int],
                           width: int, height: int,
                           confidence: float) -> None:
        """保存匹配结果可视化"""
        if not self._debug_mode or not self._debug_dir:
            return
        
        try:
            # 复制截图，在上面绘制矩形
            vis_image = screenshot.copy()
            top_left = location
            bottom_right = (location[0] + width, location[1] + height)
            
            # 绘制绿色矩形
            cv2.rectangle(vis_image, top_left, bottom_right, (0, 255, 0), 2)
            
            # 绘制中心点
            center = (location[0] + width // 2, location[1] + height // 2)
            cv2.circle(vis_image, center, 5, (0, 0, 255), -1)
            
            # 添加置信度文字
            text = f"Confidence: {confidence:.3f}"
            cv2.putText(vis_image, text, (location[0], location[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            self._save_debug_image("match_result.png", vis_image)
        except Exception as e:
            print(f"[图像识别] 保存匹配结果失败: {e}")
    
    def clear_cache(self) -> None:
        """清除模板缓存"""
        self._template_cache.clear()
        print("[图像识别] 模板缓存已清除")
    
    def get_template_info(self, name: str) -> Optional[dict]:
        """获取模板信息"""
        template = self.load_template(name)
        if template is None:
            return None
        
        return {
            "name": name,
            "width": template.shape[1],
            "height": template.shape[0],
            "channels": template.shape[2] if len(template.shape) > 2 else 1,
            "path": str(self.templates_dir / f"{name}.png")
        }
    
    def test_match(self, name: str, threshold: float = DEFAULT_THRESHOLD) -> dict:
        """
        测试模板匹配（用于调试）
        
        返回详细的匹配信息
        """
        template = self.load_template(name)
        if template is None:
            return {"error": "模板不存在", "name": name}
        
        screenshot = self._take_screenshot()
        if screenshot is None:
            return {"error": "截图失败", "name": name}
        
        result = {
            "name": name,
            "template_size": f"{template.shape[1]}x{template.shape[0]}",
            "screenshot_size": f"{screenshot.shape[1]}x{screenshot.shape[0]}",
            "threshold": threshold,
            "methods": {}
        }
        
        # 测试标准匹配
        std_result = self._match_template_standard(screenshot, template, threshold)
        result["methods"]["standard"] = {
            "found": std_result.found,
            "confidence": round(std_result.confidence, 4),
            "position": std_result.position
        }
        
        # 测试多尺度匹配
        ms_result = self._match_template_multi_scale(screenshot, template, threshold)
        result["methods"]["multi_scale"] = {
            "found": ms_result.found,
            "confidence": round(ms_result.confidence, 4),
            "position": ms_result.position,
            "scale": round(ms_result.scale, 2)
        }
        
        # 测试灰度匹配
        gray_result = self._match_template_grayscale(screenshot, template, threshold * 0.95)
        result["methods"]["grayscale"] = {
            "found": gray_result.found,
            "confidence": round(gray_result.confidence, 4),
            "position": gray_result.position
        }
        
        # 测试边缘匹配
        edge_result = self._match_template_edge(screenshot, template, self.EDGE_THRESHOLD)
        result["methods"]["edge"] = {
            "found": edge_result.found,
            "confidence": round(edge_result.confidence, 4),
            "position": edge_result.position
        }
        
        return result