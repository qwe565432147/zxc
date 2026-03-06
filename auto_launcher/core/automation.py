"""
自动化执行器模块
================

这个模块是整个程序的核心，负责协调各个模块完成自动化任务。
主要功能：
1. 检测RDP连接状态
2. 唤醒本地和远程电脑
3. 通过RDP在远程电脑上直接运行指定程序
"""

import time
from enum import Enum, auto
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from ..utils.image_recognition import ImageRecognizer
from ..utils.system_utils import SystemController


class ExecutionState(Enum):
    """执行状态枚举"""
    IDLE = auto()
    WAKING_LOCAL = auto()
    CHECKING_RDP = auto()
    CONNECTING_RDP = auto()
    WAKING_REMOTE = auto()
    RUNNING_PROGRAM = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class ExecutionConfig:
    """
    执行配置数据类
    
    属性：
        target_program_path: 目标程序的完整路径（远程电脑上的路径）
        rdp_window_title: RDP软件窗口标题（用于激活窗口）
        rdp_reconnect_attempts: RDP重连尝试次数
        rdp_reconnect_delay: RDP重连间隔（秒）
        wake_attempts: 唤醒尝试次数
        wake_delay: 唤醒间隔（秒）
        click_delay: 点击操作间隔（秒）
    """
    target_program_path: str = r"D:\ProgramData\Quark\auto.exe"
    rdp_window_title: str = "MobaXterm"
    rdp_reconnect_attempts: int = 3
    rdp_reconnect_delay: float = 5.0
    wake_attempts: int = 3
    wake_delay: float = 2.0
    click_delay: float = 1.0


class AutomationExecutor(QObject):
    """
    自动化执行器类
    
    执行流程：
    1. 唤醒本地电脑
    2. 检查并恢复RDP连接
    3. 唤醒远程电脑
    4. 使用Win+R运行目标程序
    """
    
    state_changed = Signal(ExecutionState, str)
    progress_updated = Signal(int, int, str)
    error_occurred = Signal(str)
    execution_completed = Signal(bool)
    log_message = Signal(str)
    
    TOTAL_STEPS = 5
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        super().__init__()
        self._config = config or ExecutionConfig()
        self._recognizer = ImageRecognizer()
        self._controller = SystemController()
        self._current_state = ExecutionState.IDLE
        self._current_step = 0
        self._is_executing = False
    
    @property
    def current_state(self) -> ExecutionState:
        return self._current_state
    
    @property
    def is_executing(self) -> bool:
        return self._is_executing
    
    def set_config(self, config: ExecutionConfig) -> None:
        self._config = config
    
    def execute(self) -> bool:
        """
        执行完整的自动化流程
        """
        if self._is_executing:
            self._log("已有任务在执行中")
            return False
        
        self._is_executing = True
        self._current_step = 0
        
        try:
            # 步骤1：唤醒本地电脑
            if not self._step_wake_local():
                return self._finish_with_failure("唤醒本地电脑失败")
            
            # 步骤2：检查RDP状态
            rdp_status = self._step_check_rdp()
            
            # 步骤3：根据RDP状态处理
            if rdp_status == ImageRecognizer.RDP_CONNECTED:
                self._log("RDP已连接")
            elif rdp_status == ImageRecognizer.RDP_DISCONNECTED:
                if not self._step_reconnect_rdp():
                    return self._finish_with_failure("RDP重连失败")
            elif rdp_status == ImageRecognizer.RDP_SLEEPING:
                self._log("远程电脑处于休眠状态")
            else:
                self._log("RDP状态未知，尝试继续执行")
            
            # 步骤4：唤醒远程电脑
            if not self._step_wake_remote():
                return self._finish_with_failure("唤醒远程电脑失败")
            
            # 步骤5：运行目标程序
            if not self._step_run_program():
                return self._finish_with_failure("运行目标程序失败")
            
            self._finish_with_success()
            return True
            
        except Exception as e:
            self._log(f"执行过程发生异常: {e}")
            return self._finish_with_failure(str(e))
    
    def stop(self) -> None:
        self._is_executing = False
        self._set_state(ExecutionState.IDLE, "已停止")
    
    def _step_wake_local(self) -> bool:
        """步骤1：唤醒本地电脑"""
        self._set_state(ExecutionState.WAKING_LOCAL, "正在唤醒本地电脑...")
        self._update_progress(1, "唤醒本地电脑")
        
        self._controller.prevent_sleep()
        self._log("已设置防止系统休眠")
        
        for attempt in range(self._config.wake_attempts):
            if not self._is_executing:
                return False
            
            self._log(f"尝试唤醒本地电脑 ({attempt + 1}/{self._config.wake_attempts})")
            self._controller.wake_up_screen()
            time.sleep(0.5)
            self._controller.move_to(100, 100)
            self._controller.move_to(200, 200)
            time.sleep(self._config.wake_delay)
        
        self._log("本地电脑已唤醒")
        return True
    
    def _step_check_rdp(self) -> str:
        """步骤2：检查RDP状态"""
        self._set_state(ExecutionState.CHECKING_RDP, "正在检查RDP状态...")
        self._update_progress(2, "检查RDP状态")
        
        self._log("检测RDP连接状态...")
        status = self._recognizer.check_rdp_status()
        self._log(f"RDP状态检测结果: {status}")
        return status
    
    def _step_reconnect_rdp(self) -> bool:
        """步骤3：重连RDP"""
        self._set_state(ExecutionState.CONNECTING_RDP, "正在重连RDP...")
        self._update_progress(3, "重连RDP")
        
        for attempt in range(self._config.rdp_reconnect_attempts):
            if not self._is_executing:
                return False
            
            self._log(f"尝试重连RDP ({attempt + 1}/{self._config.rdp_reconnect_attempts})")
            
            result = self._recognizer.find_template_by_name("rdp_reconnect_button")
            if result.found:
                self._log(f"找到重连按钮，位置: {result.position}")
                self._controller.click_at(*result.position, delay=1.0)
            else:
                self._log("未找到重连按钮，尝试双击屏幕中心")
                screen_width, screen_height = self._controller.get_screen_size()
                center_x, center_y = screen_width // 2, screen_height // 2
                self._controller.double_click_at(center_x, center_y, delay=1.0)
            
            time.sleep(self._config.rdp_reconnect_delay)
            
            new_status = self._recognizer.check_rdp_status()
            if new_status == ImageRecognizer.RDP_CONNECTED:
                self._log("RDP重连成功")
                return True
        
        return False
    
    def _step_wake_remote(self) -> bool:
        """步骤4：唤醒远程电脑"""
        self._set_state(ExecutionState.WAKING_REMOTE, "正在唤醒远程电脑...")
        self._update_progress(4, "唤醒远程电脑")
        
        screen_width, screen_height = self._controller.get_screen_size()
        center_x, center_y = screen_width // 2, screen_height // 2
        
        self._log("确保RDP窗口处于活动状态")
        if self._config.rdp_window_title:
            if self._controller.activate_window_by_title(self._config.rdp_window_title):
                time.sleep(0.5)
        
        self._log(f"点击RDP窗口中心 ({center_x}, {center_y}) 确保焦点在远程桌面")
        self._controller.click_at(center_x, center_y, delay=0.5)
        
        time.sleep(1)
        self._log("远程电脑已准备就绪")
        return True
    
    def _step_run_program(self) -> bool:
        """步骤5：使用Win+R运行目标程序"""
        self._set_state(ExecutionState.RUNNING_PROGRAM, "正在运行目标程序...")
        self._update_progress(5, f"运行: {Path(self._config.target_program_path).name}")
        
        screen_width, screen_height = self._controller.get_screen_size()
        center_x, center_y = screen_width // 2, screen_height // 2
        
        self._log("确保焦点在RDP窗口")
        self._controller.click_at(center_x, center_y, delay=0.3)
        time.sleep(0.3)
        
        self._log("按 Win+R 打开运行对话框")
        self._controller.hotkey('win', 'r')
        time.sleep(1.0)
        
        self._log(f"输入程序路径: {self._config.target_program_path}")
        self._controller.type_text_chinese(self._config.target_program_path)
        time.sleep(0.5)
        
        self._log("按回车运行程序")
        self._controller.press_key('enter')
        time.sleep(2)
        
        self._log(f"程序 {self._config.target_program_path} 已启动")
        return True
    
    def _set_state(self, state: ExecutionState, description: str) -> None:
        self._current_state = state
        self.state_changed.emit(state, description)
    
    def _update_progress(self, step: int, description: str) -> None:
        self._current_step = step
        self.progress_updated.emit(step, self.TOTAL_STEPS, description)
    
    def _log(self, message: str) -> None:
        self.log_message.emit(message)
    
    def _finish_with_success(self) -> None:
        self._set_state(ExecutionState.COMPLETED, "执行完成")
        self._is_executing = False
        self.execution_completed.emit(True)
        self._log("执行成功完成!")
    
    def _finish_with_failure(self, error: str) -> bool:
        self._set_state(ExecutionState.FAILED, f"执行失败: {error}")
        self._is_executing = False
        self.error_occurred.emit(error)
        self.execution_completed.emit(False)
        return False
