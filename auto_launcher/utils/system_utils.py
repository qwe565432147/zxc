"""
系统控制模块
============

提供系统级操作功能，包括：
1. 窗口管理（查找、激活、绑定）
2. 键鼠操作（使用pydirectinput，支持DirectX游戏）
3. 系统唤醒功能
"""

import time
import ctypes
from typing import Optional, Tuple
from dataclasses import dataclass

import cv2
import pydirectinput
import win32gui
import win32con
import win32api
import win32process
import numpy as np


@dataclass
class WindowInfo:
    """窗口信息数据类"""
    hwnd: int
    title: str
    class_name: str
    rect: Tuple[int, int, int, int]
    width: int
    height: int
    process_id: int


class WindowController:
    """窗口控制器 - 管理窗口绑定和操作"""
    
    def __init__(self):
        self._bound_window: Optional[WindowInfo] = None
    
    @property
    def bound_window(self) -> Optional[WindowInfo]:
        return self._bound_window
    
    @property
    def is_bound(self) -> bool:
        return self._bound_window is not None
    
    def get_window_at_cursor(self) -> Optional[WindowInfo]:
        """获取鼠标当前位置下的窗口"""
        try:
            cursor_pos = win32api.GetCursorPos()
            hwnd = win32gui.WindowFromPoint(cursor_pos)
            
            while win32gui.GetParent(hwnd) != 0:
                hwnd = win32gui.GetParent(hwnd)
            
            return self._get_window_info(hwnd)
        except Exception:
            return None
    
    def _get_window_info(self, hwnd: int) -> Optional[WindowInfo]:
        """获取窗口详细信息"""
        try:
            title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            _, process_id = win32process.GetWindowThreadProcessId(hwnd)
            
            return WindowInfo(
                hwnd=hwnd,
                title=title,
                class_name=class_name,
                rect=rect,
                width=rect[2] - rect[0],
                height=rect[3] - rect[1],
                process_id=process_id
            )
        except Exception:
            return None
    
    def bind_window(self, hwnd: int = None) -> Optional[WindowInfo]:
        """绑定窗口"""
        if hwnd:
            self._bound_window = self._get_window_info(hwnd)
        else:
            self._bound_window = self.get_window_at_cursor()
        
        return self._bound_window
    
    def unbind_window(self) -> None:
        """解绑窗口"""
        self._bound_window = None
    
    def find_window_by_title(self, title: str) -> Optional[WindowInfo]:
        """通过标题查找窗口"""
        try:
            hwnd = win32gui.FindWindow(None, title)
            if hwnd:
                return self._get_window_info(hwnd)
        except Exception:
            pass
        return None
    
    def find_window_by_class(self, class_name: str) -> Optional[WindowInfo]:
        """通过类名查找窗口"""
        try:
            hwnd = win32gui.FindWindow(class_name, None)
            if hwnd:
                return self._get_window_info(hwnd)
        except Exception:
            pass
        return None
    
    def activate_window(self, hwnd: int = None) -> bool:
        """激活窗口并置于前台"""
        if hwnd is None and self._bound_window:
            hwnd = self._bound_window.hwnd
        
        if not hwnd:
            return False
        
        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.3)
            
            if not win32gui.IsWindowVisible(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                time.sleep(0.1)
            
            try:
                foreground_hwnd = win32gui.GetForegroundWindow()
                foreground_thread = win32process.GetWindowThreadProcessId(foreground_hwnd)[0]
                current_thread = win32api.GetCurrentThreadId()
                target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
                
                if current_thread != foreground_thread:
                    ctypes.windll.user32.AttachThreadInput(current_thread, foreground_thread, True)
                if target_thread != foreground_thread and target_thread != current_thread:
                    ctypes.windll.user32.AttachThreadInput(target_thread, foreground_thread, True)
                
                win32gui.BringWindowToTop(hwnd)
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                win32gui.SetFocus(hwnd)
                
                if current_thread != foreground_thread:
                    ctypes.windll.user32.AttachThreadInput(current_thread, foreground_thread, False)
                if target_thread != foreground_thread and target_thread != current_thread:
                    ctypes.windll.user32.AttachThreadInput(target_thread, foreground_thread, False)
            except:
                pass
            
            if win32gui.GetForegroundWindow() != hwnd:
                keybd_event = ctypes.windll.user32.keybd_event
                keybd_event(0x12, 0, 0, 0)
                keybd_event(0x12, 0, 2, 0)
                
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                
                keybd_event(0x12, 0, 0, 0)
                keybd_event(0x12, 0, 2, 0)
            
            time.sleep(0.2)
            return win32gui.GetForegroundWindow() == hwnd
        except Exception as e:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(hwnd)
                return True
            except:
                return False
    
    def get_client_rect(self, hwnd: int = None) -> Optional[Tuple[int, int, int, int]]:
        """获取窗口客户区矩形"""
        if hwnd is None and self._bound_window:
            hwnd = self._bound_window.hwnd
        
        if not hwnd:
            return None
        
        try:
            return win32gui.GetClientRect(hwnd)
        except Exception:
            return None
    
    def client_to_screen(self, x: int, y: int, hwnd: int = None) -> Tuple[int, int]:
        """客户区坐标转屏幕坐标"""
        if hwnd is None and self._bound_window:
            hwnd = self._bound_window.hwnd
        
        if not hwnd:
            return (x, y)
        
        try:
            point = win32gui.ClientToScreen(hwnd, (x, y))
            return point
        except Exception:
            return (x, y)
    
    def capture_window(self, hwnd: int = None) -> Optional[np.ndarray]:
        """
        截取绑定窗口的客户区图像
        
        使用mss库进行高效截图，支持多显示器环境。
        
        返回：
            OpenCV格式的图像数组 (BGR)，如果失败返回None
            图像坐标原点为客户区左上角(0,0)
        """
        if hwnd is None and self._bound_window:
            hwnd = self._bound_window.hwnd
        
        if not hwnd:
            return None
        
        try:
            # 获取客户区尺寸
            client_left, client_top, client_right, client_bottom = win32gui.GetClientRect(hwnd)
            width = client_right - client_left
            height = client_bottom - client_top
            
            if width <= 0 or height <= 0:
                print(f"[窗口截图] 客户区尺寸无效: {width}x{height}")
                return None
            
            # 获取客户区在屏幕上的位置（支持多显示器，包括负坐标）
            screen_left, screen_top = win32gui.ClientToScreen(hwnd, (client_left, client_top))
            
            # 使用mss进行高效截图
            import mss
            
            with mss.mss() as sct:
                # mss使用的monitor格式: {'left': x, 'top': y, 'width': w, 'height': h}
                monitor = {
                    'left': screen_left,
                    'top': screen_top,
                    'width': width,
                    'height': height
                }
                
                # 截图并转换为numpy数组
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
                
                # mss返回的是BGRA格式，转换为BGR
                img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
                
                return img
            
        except Exception as e:
            print(f"[窗口截图] 截图失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def show_window(self, hwnd: int = None) -> bool:
        """显示被隐藏的窗口"""
        if hwnd is None and self._bound_window:
            hwnd = self._bound_window.hwnd
        
        if not hwnd:
            return False
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception:
            return False
    
    def hide_window(self, hwnd: int = None) -> bool:
        """隐藏窗口"""
        if hwnd is None and self._bound_window:
            hwnd = self._bound_window.hwnd
        
        if not hwnd:
            return False
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
            return True
        except Exception:
            return False


class InputController:
    """输入控制器 - 使用pydirectinput进行键鼠操作"""
    
    def __init__(self, window_controller: WindowController = None):
        self._window = window_controller or WindowController()
        pydirectinput.PAUSE = 0.05
    
    def _ensure_window_active(self) -> bool:
        """确保绑定窗口处于活动状态"""
        if self._window.is_bound:
            return self._window.activate_window()
        return True
    
    def click_at(self, x: int, y: int, relative: bool = True, delay: float = 0.1) -> bool:
        """
        点击指定位置
        
        参数：
            x, y: 坐标
            relative: 是否相对于绑定窗口客户区
            delay: 点击后延迟
        """
        try:
            if relative and self._window.is_bound:
                screen_x, screen_y = self._window.client_to_screen(x, y)
            else:
                screen_x, screen_y = x, y
            
            self._ensure_window_active()
            pydirectinput.moveTo(screen_x, screen_y)
            time.sleep(0.05)
            pydirectinput.click()
            time.sleep(delay)
            return True
        except Exception:
            return False
    
    def click_center(self, delay: float = 0.1) -> bool:
        """点击绑定窗口中心"""
        if not self._window.is_bound:
            return False
        
        rect = self._window.get_client_rect()
        if not rect:
            return False
        
        center_x = (rect[2] - rect[0]) // 2
        center_y = (rect[3] - rect[1]) // 2
        
        return self.click_at(center_x, center_y, relative=True, delay=delay)
    
    def double_click_at(self, x: int, y: int, relative: bool = True, delay: float = 0.1) -> bool:
        """双击指定位置"""
        try:
            if relative and self._window.is_bound:
                screen_x, screen_y = self._window.client_to_screen(x, y)
            else:
                screen_x, screen_y = x, y
            
            self._ensure_window_active()
            pydirectinput.moveTo(screen_x, screen_y)
            time.sleep(0.05)
            pydirectinput.doubleClick()
            time.sleep(delay)
            return True
        except Exception:
            return False
    
    def move_to(self, x: int, y: int, relative: bool = True) -> bool:
        """移动鼠标到指定位置"""
        try:
            if relative and self._window.is_bound:
                screen_x, screen_y = self._window.client_to_screen(x, y)
            else:
                screen_x, screen_y = x, y
            
            pydirectinput.moveTo(screen_x, screen_y)
            return True
        except Exception:
            return False
    
    def press_key(self, key: str, delay: float = 0.1) -> bool:
        """按下并释放按键"""
        try:
            self._ensure_window_active()
            pydirectinput.press(key)
            time.sleep(delay)
            return True
        except Exception:
            return False
    
    def key_down(self, key: str) -> bool:
        """按下按键"""
        try:
            self._ensure_window_active()
            pydirectinput.keyDown(key)
            return True
        except Exception:
            return False
    
    def key_up(self, key: str) -> bool:
        """释放按键"""
        try:
            pydirectinput.keyUp(key)
            return True
        except Exception:
            return False
    
    def hotkey(self, *keys: str, delay: float = 0.1) -> bool:
        """发送组合键"""
        try:
            self._ensure_window_active()
            
            for key in keys:
                pydirectinput.keyDown(key)
                time.sleep(0.02)
            
            time.sleep(0.05)
            
            for key in reversed(keys):
                pydirectinput.keyUp(key)
                time.sleep(0.02)
            
            time.sleep(delay)
            return True
        except Exception:
            return False
    
    def type_text(self, text: str, delay: float = 0.05) -> bool:
        """输入文本（仅支持ASCII字符）"""
        try:
            self._ensure_window_active()
            for char in text:
                if char.isupper():
                    pydirectinput.keyDown('shift')
                    pydirectinput.press(char.lower())
                    pydirectinput.keyUp('shift')
                elif char == ' ':
                    pydirectinput.press('space')
                elif char == '\n':
                    pydirectinput.press('enter')
                elif char == '\t':
                    pydirectinput.press('tab')
                else:
                    pydirectinput.press(char)
                time.sleep(delay)
            return True
        except Exception:
            return False
    
    def type_text_chinese(self, text: str, delay: float = 0.1) -> bool:
        """
        输入中文文本（通过剪贴板）
        pydirectinput不支持直接输入中文，使用剪贴板粘贴
        """
        try:
            self._ensure_window_active()
            
            import pyperclip
            pyperclip.copy(text)
            time.sleep(0.1)
            
            return self.hotkey('ctrl', 'v', delay=delay)
        except Exception:
            return False
    
    def scroll(self, clicks: int = 1, delay: float = 0.1) -> bool:
        """滚动鼠标滚轮"""
        try:
            self._ensure_window_active()
            pydirectinput.scroll(clicks)
            time.sleep(delay)
            return True
        except Exception:
            return False


class SystemController:
    """系统控制器 - 整合窗口和输入控制"""
    
    def __init__(self):
        self.window = WindowController()
        self.input = InputController(self.window)
    
    def bind_window_at_cursor(self) -> Optional[WindowInfo]:
        """绑定鼠标下的窗口"""
        return self.window.bind_window()
    
    def bind_window_by_title(self, title: str) -> Optional[WindowInfo]:
        """通过标题绑定窗口"""
        window_info = self.window.find_window_by_title(title)
        if window_info:
            self.window.bind_window(window_info.hwnd)
        return window_info
    
    def unbind_window(self) -> None:
        """解绑窗口"""
        self.window.unbind_window()
    
    def get_screen_size(self) -> Tuple[int, int]:
        """获取主屏幕尺寸"""
        user32 = ctypes.windll.user32
        return (user32.GetSystemMetrics(0), user32.GetSystemMetrics(1))
    
    def get_virtual_screen_size(self) -> Tuple[int, int, int, int]:
        """
        获取虚拟屏幕尺寸（多显示器环境）
        
        返回:
            (left, top, width, height) 虚拟屏幕的边界
        """
        user32 = ctypes.windll.user32
        SM_XVIRTUALSCREEN = 76
        SM_YVIRTUALSCREEN = 77
        SM_CXVIRTUALSCREEN = 78
        SM_CYVIRTUALSCREEN = 79
        
        left = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
        top = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
        width = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
        height = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
        
        return (left, top, width, height)
    
    def get_mouse_position(self) -> Tuple[int, int]:
        """获取鼠标位置"""
        return win32api.GetCursorPos()
    
    def wake_up_screen(self) -> bool:
        """唤醒屏幕"""
        try:
            user32 = ctypes.windll.user32
            
            user32.mouse_event(0x0001, 0, 0, 0, 0)
            user32.mouse_event(0x0001, 0, 0, 0, 0)
            
            user32.keybd_event(0, 0, 0, 0)
            user32.keybd_event(0, 0, 2, 0)
            
            return True
        except Exception:
            return False
    
    def prevent_sleep(self) -> None:
        """防止系统休眠"""
        ES_CONTINUOUS = 0x80000000
        ES_SYSTEM_REQUIRED = 0x00000001
        ES_DISPLAY_REQUIRED = 0x00000002
        
        ctypes.windll.kernel32.SetThreadExecutionState(
            ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
        )
    
    def allow_sleep(self) -> None:
        """允许系统休眠"""
        ES_CONTINUOUS = 0x80000000
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
    
    @property
    def bound_window(self) -> Optional[WindowInfo]:
        return self.window.bound_window
    
    @property
    def is_window_bound(self) -> bool:
        return self.window.is_bound