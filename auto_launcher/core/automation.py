"""
自动化执行器模块
"""

import time
import ctypes
from enum import Enum, auto
from typing import Optional, Dict
from dataclasses import dataclass
from pathlib import Path

import win32gui
import win32con

from PySide6.QtCore import QObject, Signal

from ..utils.image_recognition import ImageRecognizer
from ..utils.system_utils import SystemController


class ExecutionState(Enum):
    IDLE = auto()
    WAKING_LOCAL = auto()
    WAKING_REMOTE = auto()
    RUNNING_PROGRAM = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class ExecutionConfig:
    target_program_path: str = r"D:\ProgramData\Quark\auto.exe"
    rdp_reconnect_attempts: int = 3
    rdp_reconnect_delay: float = 5.0
    wake_attempts: int = 3
    wake_delay: float = 1.0
    click_delay: float = 1.0


class AutomationExecutor(QObject):
    state_changed = Signal(ExecutionState, str)
    progress_updated = Signal(int, int, str)
    error_occurred = Signal(str)
    execution_completed = Signal(bool)
    log_message = Signal(str)
    
    TOTAL_STEPS = 4
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        super().__init__()
        self._config = config or ExecutionConfig()
        self._recognizer = ImageRecognizer()
        self._controller = SystemController()
        self._current_state = ExecutionState.IDLE
        self._is_executing = False
        self._bound_window: Optional[Dict] = None
    
    @property
    def current_state(self) -> ExecutionState:
        return self._current_state
    
    @property
    def is_executing(self) -> bool:
        return self._is_executing
    
    def set_config(self, config: ExecutionConfig) -> None:
        self._config = config
    
    def set_bound_window(self, window_info: Dict) -> None:
        self._bound_window = window_info
        hwnd = window_info.get('hwnd')
        if hwnd:
            self._controller.window.bind_window(hwnd)
            self._recognizer.set_window_capture(
                lambda: self._controller.window.capture_window(hwnd)
            )
            self._log(f"已绑定窗口: {window_info.get('title', '未知')}")
    
    def clear_bound_window(self) -> None:
        self._bound_window = None
        self._controller.unbind_window()
        self._recognizer.set_window_capture(None)
    
    def execute(self) -> bool:
        if self._is_executing:
            return False
        
        self._is_executing = True
        
        try:
            # 步骤1: 唤醒本地 (25%)
            self._set_state(ExecutionState.WAKING_LOCAL, "唤醒本地...")
            self.progress_updated.emit(25, 100, "唤醒本地")
            self._controller.prevent_sleep()
            self._controller.wake_up_screen()
            time.sleep(0.3)
            
            # 步骤2: 激活窗口 (50%)
            self.progress_updated.emit(50, 100, "激活窗口")
            if self._controller.is_window_bound:
                self._activate_window()
            
            # 步骤3: 检查RDP状态 (75%)
            self._set_state(ExecutionState.WAKING_REMOTE, "检查远程...")
            self.progress_updated.emit(75, 100, "检查远程")
            if self._controller.is_window_bound:
                rdp_status = self._recognizer.check_rdp_status()
                if rdp_status != ImageRecognizer.RDP_CONNECTED:
                    self._handle_rdp_issue(rdp_status)
            
            # 步骤4: 运行程序 (100%)
            self._set_state(ExecutionState.RUNNING_PROGRAM, "运行程序...")
            self.progress_updated.emit(100, 100, "运行程序")
            self._run_program()
            
            self._finish_with_success()
            return True
            
        except Exception as e:
            self._log(f"执行异常: {e}")
            return self._finish_with_failure(str(e))
    
    def stop(self) -> None:
        self._is_executing = False
        self._set_state(ExecutionState.IDLE, "已停止")
    
    def _activate_window(self) -> None:
        """激活绑定窗口"""
        try:
            hwnd = self._controller.window.bound_window.hwnd
            if not win32gui.IsWindow(hwnd):
                raise Exception("窗口已关闭")
            
            # 获取顶层窗口
            top_hwnd = self._get_top_parent(hwnd)
            
            # 恢复并激活
            if win32gui.IsIconic(top_hwnd):
                win32gui.ShowWindow(top_hwnd, win32con.SW_RESTORE)
            
            win32gui.ShowWindow(top_hwnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(top_hwnd)
            
            # 聚焦子窗口
            if top_hwnd != hwnd:
                self._click_window_center(hwnd)
            
            time.sleep(0.2)
            self._log("窗口已激活")
        except Exception as e:
            self._log(f"窗口激活: {e}")
    
    def _get_top_parent(self, hwnd: int) -> int:
        """获取顶层父窗口"""
        try:
            GA_ROOT = 2
            return ctypes.windll.user32.GetAncestor(hwnd, GA_ROOT) or hwnd
        except:
            return hwnd
    
    def _click_window_center(self, hwnd: int) -> None:
        """点击窗口中心"""
        try:
            rect = win32gui.GetWindowRect(hwnd)
            x = (rect[0] + rect[2]) // 2
            y = (rect[1] + rect[3]) // 2
            ctypes.windll.user32.SetCursorPos(x, y)
            time.sleep(0.05)
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
        except:
            pass
    
    def _handle_rdp_issue(self, status: str) -> None:
        """处理RDP问题"""
        self._log(f"RDP状态: {status}")
        
        if status == ImageRecognizer.RDP_DISCONNECTED:
            # 尝试点击重连按钮
            for _ in range(self._config.rdp_reconnect_attempts):
                result = self._recognizer.find_template_by_name("rdp_reconnect_button", 0.8)
                if result.found:
                    self._controller.input.click_at(result.position[0], result.position[1], relative=True)
                    time.sleep(self._config.rdp_reconnect_delay)
                    if self._recognizer.check_rdp_status() == ImageRecognizer.RDP_CONNECTED:
                        return
                else:
                    self._controller.input.click_center()
                    time.sleep(self._config.rdp_reconnect_delay)
        
        elif status == ImageRecognizer.RDP_SLEEPING:
            # 唤醒远程电脑
            self._controller.input.press_key('space')
            time.sleep(0.5)
            self._controller.input.press_key('enter')
            time.sleep(2)
    
    def _run_program(self) -> None:
        """运行目标程序"""
        import pyperclip
        
        self._log(f"运行: {self._config.target_program_path}")
        pyperclip.copy(self._config.target_program_path)
        
        for attempt in range(2):
            # 激活窗口
            if self._controller.is_window_bound:
                self._controller.window.activate_window()
                time.sleep(0.1)
                self._controller.input.click_center(delay=0.05)
            
            # Ctrl+Esc 打开开始菜单
            self._send_keys('ctrl', 'esc', separate=True)
            time.sleep(0.3)
            
            # 粘贴路径
            self._send_keys('ctrl', 'v', separate=True)
            time.sleep(0.2)
            
            # 回车执行
            self._send_key('enter')
            time.sleep(0.3)
            
            # ESC关闭菜单
            self._send_key('escape')
            
            self._log(f"运行命令已发送 ({attempt + 1}/2)")
            
            if self._controller.is_window_bound:
                if self._recognizer.check_rdp_status() == ImageRecognizer.RDP_CONNECTED:
                    return
    
    def _send_key(self, key: str) -> None:
        """发送单个按键"""
        import pydirectinput
        pydirectinput.press(key)
    
    def _send_keys(self, *keys: str, separate: bool = False) -> None:
        """发送组合键"""
        import pydirectinput
        
        if separate:
            # 组合键
            for key in keys[:-1]:
                pydirectinput.keyDown(key)
                time.sleep(0.02)
            pydirectinput.press(keys[-1])
            time.sleep(0.02)
            for key in reversed(keys[:-1]):
                pydirectinput.keyUp(key)
        else:
            for key in keys:
                pydirectinput.press(key)
    
    def _set_state(self, state: ExecutionState, desc: str) -> None:
        self._current_state = state
        self.state_changed.emit(state, desc)
    
    def _log(self, msg: str) -> None:
        self.log_message.emit(msg)
    
    def _finish_with_success(self) -> None:
        self._set_state(ExecutionState.COMPLETED, "完成")
        self._is_executing = False
        self.execution_completed.emit(True)
        self._log("执行完成!")
    
    def _finish_with_failure(self, error: str) -> bool:
        self._set_state(ExecutionState.FAILED, f"失败: {error}")
        self._is_executing = False
        self.error_occurred.emit(error)
        self.execution_completed.emit(False)
        return False