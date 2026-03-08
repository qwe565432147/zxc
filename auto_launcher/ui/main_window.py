"""
主窗口模块
==========

这个模块实现了程序的主界面，包括：
1. 窗口绑定控件（拖拽绑定）
2. 倒计时设置面板
3. 目标程序路径输入
4. 状态显示面板
5. 控制按钮
6. 日志显示区域
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QSpinBox, QPushButton,
    QTextEdit, QProgressBar, QFrame, QSizePolicy,
    QLineEdit, QComboBox, QStyle, QStyleOptionSpinBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QRect
from PySide6.QtGui import QFont, QPainter, QColor, QPen, QBrush

from ..core.countdown import CountdownManager
from ..core.automation import AutomationExecutor, ExecutionConfig, ExecutionState
from .window_binder import WindowBinderPanel


class CompactSpinBox(QSpinBox):
    """紧凑型数字输入框，带自定义箭头"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(80)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QSpinBox {
                padding: 3px 25px 3px 10px;
            }
            QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: right top;
                width: 20px;
                border: none;
                border-left: 1px solid #ddd;
            }
            QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: right bottom;
                width: 20px;
                border: none;
                border-left: 1px solid #ddd;
            }
            QSpinBox::up-arrow { image: none; }
            QSpinBox::down-arrow { image: none; }
        """)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        btn_width = 20
        btn_height = self.height() // 2
        
        up_rect = QRect(self.width() - btn_width, 0, btn_width, btn_height)
        down_rect = QRect(self.width() - btn_width, btn_height, btn_width, btn_height)
        
        painter.setPen(QPen(QColor("#666666"), 2, Qt.SolidLine, Qt.RoundCap))
        painter.setBrush(Qt.NoBrush)
        
        painter.drawLine(up_rect.center().x() - 4, up_rect.center().y() + 2,
                        up_rect.center().x(), up_rect.center().y() - 2)
        painter.drawLine(up_rect.center().x(), up_rect.center().y() - 2,
                        up_rect.center().x() + 4, up_rect.center().y() + 2)
        
        painter.drawLine(down_rect.center().x() - 4, down_rect.center().y() - 2,
                        down_rect.center().x(), down_rect.center().y() + 2)
        painter.drawLine(down_rect.center().x(), down_rect.center().y() + 2,
                        down_rect.center().x() + 4, down_rect.center().y() - 2)


class MainWindow(QMainWindow):
    """
    主窗口类
    
    主要组件：
    - 窗口绑定区：拖拽绑定目标RDP窗口
    - 时间设置区：设置倒计时时间
    - 程序路径：输入要运行的程序完整路径
    - 倒计时显示：大字体显示剩余时间
    - 状态面板：显示当前状态和进度
    - 控制按钮：开始、暂停、重置等
    - 日志区域：显示操作日志
    """
    
    start_execution_requested = Signal()
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("自动化脚本启动器")
        self.setMinimumSize(520, 620)
        self.resize(560, 680)
        
        self._countdown = CountdownManager()
        self._executor = AutomationExecutor()
        self._bound_window_info = None
        
        self._init_ui()
        self._connect_signals()
        self._apply_styles()
    
    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        main_layout.addWidget(self._create_window_bind_group())
        main_layout.addWidget(self._create_time_input_group())
        main_layout.addWidget(self._create_path_input_group())
        main_layout.addWidget(self._create_countdown_display())
        main_layout.addWidget(self._create_status_group())
        main_layout.addWidget(self._create_control_buttons())
        main_layout.addWidget(self._create_log_area())
    
    def _create_window_bind_group(self) -> QGroupBox:
        """创建窗口绑定区域"""
        group = QGroupBox("窗口绑定")
        layout = QVBoxLayout(group)
        
        self.window_binder = WindowBinderPanel()
        self.window_binder.window_bound.connect(self._on_window_bound)
        self.window_binder.window_unbound.connect(self._on_window_unbound)
        layout.addWidget(self.window_binder)
        
        return group
    
    def _on_window_bound(self, window_info: dict) -> None:
        """窗口绑定成功回调"""
        self._bound_window_info = window_info
        title = window_info.get('title', '未知窗口')
        width = window_info.get('width', 0)
        height = window_info.get('height', 0)
        class_name = window_info.get('class_name', '')
        
        self._log(f"窗口绑定成功: {title}")
        self._log(f"  尺寸: {width}x{height}, 类名: {class_name}")
        
        self._executor.set_bound_window(window_info)
    
    def _on_window_unbound(self) -> None:
        """窗口解除绑定回调"""
        self._bound_window_info = None
        self._log("已解除窗口绑定")
        self._executor.clear_bound_window()
    
    def _create_time_input_group(self) -> QGroupBox:
        group = QGroupBox("倒计时设置")
        layout = QHBoxLayout(group)
        layout.addStretch()
        
        self.hour_spin = CompactSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(1)
        layout.addWidget(self.hour_spin)
        layout.addWidget(QLabel("时"))
        
        self.minute_spin = CompactSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(30)
        layout.addWidget(self.minute_spin)
        layout.addWidget(QLabel("分"))
        
        self.second_spin = CompactSpinBox()
        self.second_spin.setRange(0, 59)
        self.second_spin.setValue(0)
        layout.addWidget(self.second_spin)
        layout.addWidget(QLabel("秒"))
        
        self.set_time_btn = QPushButton("设置时间")
        self.set_time_btn.setFixedWidth(90)
        layout.addWidget(self.set_time_btn)
        
        layout.addStretch()
        return group
    
    def _create_path_input_group(self) -> QGroupBox:
        group = QGroupBox("配置")
        layout = QVBoxLayout(group)
        layout.setAlignment(Qt.AlignCenter)
        
        path_layout = QHBoxLayout()
        path_layout.addStretch()
        path_layout.addWidget(QLabel("目标程序:"))
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("例如: D:\\ProgramData\\Quark\\auto.exe")
        self.path_input.setText(r"D:\ProgramData\Quark\auto.exe")
        self.path_input.setMinimumWidth(300)
        path_layout.addWidget(self.path_input)
        path_layout.addStretch()
        layout.addLayout(path_layout)
        
        return group
    
    def _create_countdown_display(self) -> QFrame:
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setFrameShadow(QFrame.Raised)
        frame.setMinimumHeight(100)
        
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(15, 5, 15, 5)
        
        title_label = QLabel("剩余时间")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        self.countdown_label = QLabel("00:00:00")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        font = QFont("Consolas", 42, QFont.Bold)
        self.countdown_label.setFont(font)
        layout.addWidget(self.countdown_label)
        
        return frame
    
    def _create_status_group(self) -> QGroupBox:
        group = QGroupBox("执行状态")
        layout = QVBoxLayout(group)
        
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("当前状态:"))
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("执行进度:"))
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMinimumHeight(28)
        progress_layout.addWidget(self.progress_bar, 1)
        layout.addLayout(progress_layout)
        
        self.completion_widget = QWidget()
        completion_layout = QHBoxLayout(self.completion_widget)
        completion_layout.setContentsMargins(0, 0, 0, 0)
        completion_layout.setSpacing(8)
        
        self.completion_icon = QLabel()
        self.completion_icon.setFixedSize(22, 22)
        self.completion_icon.setStyleSheet("""
            QLabel {
                background-color: #4CAF50;
                border-radius: 11px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.completion_icon.setText("✓")
        self.completion_icon.setAlignment(Qt.AlignCenter)
        completion_layout.addWidget(self.completion_icon)
        
        self.completion_label = QLabel("任务已自动化执行完毕")
        self.completion_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 13px;")
        completion_layout.addWidget(self.completion_label)
        completion_layout.addStretch()
        
        self.completion_widget.setVisible(False)
        layout.addWidget(self.completion_widget)
        
        return group
    
    def _create_control_buttons(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 5)
        
        self.start_btn = QPushButton("▶ 开始")
        self.start_btn.setFixedHeight(35)
        self.start_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("⏸ 暂停")
        self.pause_btn.setFixedHeight(35)
        self.pause_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.pause_btn.setEnabled(False)
        layout.addWidget(self.pause_btn)
        
        self.reset_btn = QPushButton("⏹ 重置")
        self.reset_btn.setFixedHeight(35)
        self.reset_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.reset_btn)
        
        self.screenshot_btn = QPushButton("⚙ 模板配置")
        self.screenshot_btn.setFixedHeight(35)
        self.screenshot_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.screenshot_btn)
        
        return widget
    
    def _create_log_area(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("操作日志:"))
        
        self.clear_log_btn = QPushButton("清除日志")
        self.clear_log_btn.setFixedSize(80, 28)
        header_layout.addWidget(self.clear_log_btn)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(75)
        self.log_text.setMaximumHeight(100)
        layout.addWidget(self.log_text)
        
        return widget
    
    def _connect_signals(self) -> None:
        self.set_time_btn.clicked.connect(self._on_set_time)
        self.start_btn.clicked.connect(self._on_start)
        self.pause_btn.clicked.connect(self._on_pause)
        self.reset_btn.clicked.connect(self._on_reset)
        self.clear_log_btn.clicked.connect(self.log_text.clear)
        self.screenshot_btn.clicked.connect(self._on_screenshot_clicked)
        
        self._countdown.time_updated.connect(self._on_countdown_updated)
        self._countdown.countdown_finished.connect(self._on_countdown_finished)
        
        self._executor.state_changed.connect(self._on_execution_state_changed)
        self._executor.progress_updated.connect(self._on_progress_updated)
        self._executor.log_message.connect(self._log)
        self._executor.execution_completed.connect(self._on_execution_completed)
    
    def _on_set_time(self) -> None:
        hours = self.hour_spin.value()
        minutes = self.minute_spin.value()
        seconds = self.second_spin.value()
        
        self._countdown.set_countdown(hours, minutes, seconds)
        self._log(f"设置倒计时: {hours}时{minutes}分{seconds}秒")
        
        self.countdown_label.setText(self._countdown.format_time(self._countdown.remaining_seconds))
    
    def _on_start(self) -> None:
        if self._countdown.is_running:
            self._log("倒计时已在运行中")
            return
        
        if self._countdown.remaining_seconds <= 0:
            self._log("请先设置倒计时时间")
            return
        
        if not self._bound_window_info:
            self._log("警告: 未绑定窗口，操作可能不稳定")
        
        self._countdown.start()
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self._log("倒计时已开始")
    
    def _on_pause(self) -> None:
        if self._countdown.is_running:
            self._countdown.pause()
            self.start_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self._log("倒计时已暂停")
    
    def _on_reset(self) -> None:
        self._countdown.reset()
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("就绪")
        self.status_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        self._log("已重置")
    
    def _on_countdown_updated(self, seconds: int) -> None:
        time_str = CountdownManager.format_time(seconds)
        self.countdown_label.setText(time_str)
        if seconds <= 60:
            self.countdown_label.setStyleSheet("color: #F44336;")
        elif seconds <= 300:
            self.countdown_label.setStyleSheet("color: #FF9800;")
        else:
            self.countdown_label.setStyleSheet("")
    
    def _on_countdown_finished(self) -> None:
        self._log("倒计时结束，开始执行自动化任务...")
        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(False)
        self._execute_automation()
    
    def _on_execution_state_changed(self, state: ExecutionState, message: str) -> None:
        self.status_label.setText(message)
        
        state_colors = {
            ExecutionState.IDLE: "#2196F3",
            ExecutionState.WAKING_LOCAL: "#FF9800",
            ExecutionState.WAKING_REMOTE: "#FF9800",
            ExecutionState.RUNNING_PROGRAM: "#4CAF50",
            ExecutionState.COMPLETED: "#4CAF50",
            ExecutionState.FAILED: "#F44336",
        }
        color = state_colors.get(state, "#2196F3")
        self.status_label.setStyleSheet(f"font-weight: bold; color: {color};")
    
    def _on_progress_updated(self, step: int, total: int, message: str) -> None:
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(step)
    
    def _on_execution_completed(self, success: bool) -> None:
        if success:
            self._log("自动化任务执行完成！")
            # 完成提示显示在进度条内部，使用白色文字
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("✓ 任务已自动化执行完毕")
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 4px;
                    text-align: center;
                    height: 28px;
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                    font-size: 13px;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 4px;
                }
            """)
            self.completion_widget.setVisible(False)
            self.progress_bar.setVisible(True)
        else:
            self._log("自动化任务执行失败！")
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("✗ 执行失败")
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 4px;
                    text-align: center;
                    height: 28px;
                    background-color: #F44336;
                    color: white;
                    font-weight: bold;
                    font-size: 13px;
                }
                QProgressBar::chunk {
                    background-color: #F44336;
                    border-radius: 4px;
                }
            """)
            self.completion_widget.setVisible(False)
        
        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
    
    def _log(self, message: str) -> None:
        import time
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _execute_automation(self) -> None:
        full_path = self.path_input.text().strip()
        if not full_path:
            self._log("错误：程序路径不能为空")
            return
        
        self.completion_widget.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        config = ExecutionConfig(
            target_program_path=full_path,
            rdp_reconnect_attempts=3,
            rdp_reconnect_delay=5.0,
            wake_attempts=3,
            wake_delay=2.0,
            click_delay=1.0
        )
        
        if self._bound_window_info:
            self._log(f"目标窗口: {self._bound_window_info.get('title', '未知')}")
        self._log(f"目标程序: {full_path}")
        
        self._executor.set_config(config)
        self._executor.execute()
    
    def _on_screenshot_clicked(self) -> None:
        from ..utils.screenshot_tool import TemplateCaptureWizard
        self._wizard = TemplateCaptureWizard(self)
        self._wizard.capture_completed.connect(self._on_capture_completed)
        self._wizard.show()
    
    def _on_capture_completed(self) -> None:
        self._log("模板截图完成")
    
    def _apply_styles(self) -> None:
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ddd;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:pressed { background-color: #0D47A1; }
            QPushButton:disabled { background-color: #BDBDBD; }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
                font-family: Consolas, monospace;
            }
            QLineEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QLineEdit:focus { border-color: #2196F3; }
            CompactSpinBox, QSpinBox {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 2px 20px 2px 6px;
                background-color: white;
            }
        """)
