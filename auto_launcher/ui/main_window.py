"""
主窗口模块
==========

这个模块实现了程序的主界面，包括：
1. 倒计时设置面板
2. 目标程序路径输入
3. 状态显示面板
4. 控制按钮
5. 日志显示区域
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QSpinBox, QPushButton,
    QTextEdit, QProgressBar, QFrame, QSizePolicy,
    QLineEdit, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

from ..core.countdown import CountdownManager
from ..core.automation import AutomationExecutor, ExecutionConfig, ExecutionState


class MainWindow(QMainWindow):
    """
    主窗口类
    
    主要组件：
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
        self.setMinimumSize(500, 550)
        self.resize(550, 600)
        
        self._countdown = CountdownManager()
        self._executor = AutomationExecutor()
        
        self._init_ui()
        self._connect_signals()
        self._apply_styles()
    
    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        main_layout.addWidget(self._create_time_input_group())
        main_layout.addWidget(self._create_path_input_group())
        main_layout.addWidget(self._create_countdown_display())
        main_layout.addWidget(self._create_status_group())
        main_layout.addWidget(self._create_control_buttons())
        main_layout.addWidget(self._create_log_area())
    
    def _create_time_input_group(self) -> QGroupBox:
        group = QGroupBox("倒计时设置")
        layout = QHBoxLayout(group)
        
        self.hour_spin = QSpinBox()
        self.hour_spin.setRange(0, 23)
        self.hour_spin.setValue(1)
        self.hour_spin.setFixedWidth(70)
        layout.addWidget(self.hour_spin)
        layout.addWidget(QLabel("时"))
        
        self.minute_spin = QSpinBox()
        self.minute_spin.setRange(0, 59)
        self.minute_spin.setValue(30)
        self.minute_spin.setFixedWidth(70)
        layout.addWidget(self.minute_spin)
        layout.addWidget(QLabel("分"))
        
        self.second_spin = QSpinBox()
        self.second_spin.setRange(0, 59)
        self.second_spin.setValue(0)
        self.second_spin.setFixedWidth(70)
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
        
        rdp_layout = QHBoxLayout()
        rdp_layout.addWidget(QLabel("RDP软件:"))
        self.rdp_combo = QComboBox()
        self.rdp_combo.addItems(["MobaXterm", "Xshell", "Windows远程桌面", "自定义"])
        self.rdp_combo.setCurrentText("MobaXterm")
        self.rdp_combo.setFixedWidth(150)
        self.rdp_combo.currentTextChanged.connect(self._on_rdp_changed)
        rdp_layout.addWidget(self.rdp_combo)
        
        self.custom_rdp_label = QLabel("窗口标题:")
        self.custom_rdp_label.setVisible(False)
        rdp_layout.addWidget(self.custom_rdp_label)
        
        self.custom_rdp_input = QLineEdit()
        self.custom_rdp_input.setPlaceholderText("输入RDP窗口标题")
        self.custom_rdp_input.setFixedWidth(150)
        self.custom_rdp_input.setVisible(False)
        rdp_layout.addWidget(self.custom_rdp_input)
        
        rdp_layout.addStretch()
        layout.addLayout(rdp_layout)
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("目标程序:"))
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("例如: D:\\ProgramData\\Quark\\auto.exe")
        self.path_input.setText(r"D:\ProgramData\Quark\auto.exe")
        path_layout.addWidget(self.path_input)
        layout.addLayout(path_layout)
        
        return group
    
    def _on_rdp_changed(self, text: str) -> None:
        is_custom = (text == "自定义")
        self.custom_rdp_label.setVisible(is_custom)
        self.custom_rdp_input.setVisible(is_custom)
    
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
        self.progress_bar.setRange(0, 5)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%v / %m 步")
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)
        
        rdp_layout = QHBoxLayout()
        rdp_layout.addWidget(QLabel("RDP状态:"))
        self.rdp_status_label = QLabel("未检测")
        self.rdp_status_label.setStyleSheet("color: #9E9E9E;")
        rdp_layout.addWidget(self.rdp_status_label)
        rdp_layout.addStretch()
        layout.addLayout(rdp_layout)
        
        return group
    
    def _create_control_buttons(self) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(10)
        
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
        
        self.test_btn = QPushButton("🔧 测试")
        self.test_btn.setFixedHeight(35)
        self.test_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.test_btn)
        
        self.screenshot_btn = QPushButton("⚙ 模板配置")
        self.screenshot_btn.setFixedHeight(35)
        self.screenshot_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self.screenshot_btn)
        
        return widget
    
    def _create_log_area(self) -> QGroupBox:
        group = QGroupBox("操作日志")
        layout = QVBoxLayout(group)
        layout.setSpacing(5)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(60)
        self.log_text.setMaximumHeight(80)
        log_font = QFont("Consolas", 9)
        self.log_text.setFont(log_font)
        layout.addWidget(self.log_text)
        
        clear_btn = QPushButton("清除日志")
        clear_btn.setFixedSize(80, 25)
        clear_btn.clicked.connect(self.log_text.clear)
        layout.addWidget(clear_btn, alignment=Qt.AlignRight)
        
        return group
    
    def _connect_signals(self) -> None:
        self.set_time_btn.clicked.connect(self._on_set_time_clicked)
        self.start_btn.clicked.connect(self._on_start_clicked)
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        self.test_btn.clicked.connect(self._on_test_clicked)
        self.screenshot_btn.clicked.connect(self._on_screenshot_clicked)
        
        self._countdown.time_updated.connect(self._on_countdown_updated)
        self._countdown.countdown_finished.connect(self._on_countdown_finished)
        self._countdown.status_changed.connect(self._on_countdown_status_changed)
        
        self._executor.state_changed.connect(self._on_executor_state_changed)
        self._executor.progress_updated.connect(self._on_executor_progress_updated)
        self._executor.log_message.connect(self._on_log_message)
        self._executor.error_occurred.connect(self._on_executor_error)
        self._executor.execution_completed.connect(self._on_execution_completed)
    
    def _on_set_time_clicked(self) -> None:
        hours = self.hour_spin.value()
        minutes = self.minute_spin.value()
        seconds = self.second_spin.value()
        self._countdown.set_countdown(hours, minutes, seconds)
        self._log(f"设置倒计时: {hours}时{minutes}分{seconds}秒")
    
    def _on_start_clicked(self) -> None:
        if self._countdown.is_running:
            return
        if self._countdown.remaining_seconds <= 0:
            self._on_set_time_clicked()
        if self._countdown.start():
            self._update_button_states(running=True)
            self._log("倒计时开始")
    
    def _on_pause_clicked(self) -> None:
        if self._countdown.is_paused:
            self._countdown.start()
            self.pause_btn.setText("⏸ 暂停")
            self._log("倒计时恢复")
        else:
            self._countdown.pause()
            self.pause_btn.setText("▶ 继续")
            self._log("倒计时暂停")
    
    def _on_reset_clicked(self) -> None:
        self._countdown.reset()
        self._update_button_states(running=False)
        self.progress_bar.setValue(0)
        self._log("倒计时重置")
    
    def _on_test_clicked(self) -> None:
        self._log("测试RDP状态...")
        from ..utils.image_recognition import ImageRecognizer
        recognizer = ImageRecognizer()
        status = recognizer.check_rdp_status()
        self.rdp_status_label.setText(status)
        if status == ImageRecognizer.RDP_CONNECTED:
            self.rdp_status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        elif status == ImageRecognizer.RDP_DISCONNECTED:
            self.rdp_status_label.setStyleSheet("color: #FF9800; font-weight: bold;")
        elif status == ImageRecognizer.RDP_SLEEPING:
            self.rdp_status_label.setStyleSheet("color: #F44336; font-weight: bold;")
        else:
            self.rdp_status_label.setStyleSheet("color: #9E9E9E;")
        self._log(f"RDP状态: {status}")
    
    def _on_screenshot_clicked(self) -> None:
        """打开截图向导"""
        from ..utils.screenshot_tool import TemplateCaptureWizard
        self._wizard = TemplateCaptureWizard(self)
        self._wizard.capture_completed.connect(self._on_capture_completed)
        self._wizard.show()
    
    def _on_capture_completed(self) -> None:
        """截图完成"""
        self._log("模板截图完成")
    
    def _on_countdown_updated(self, seconds: int) -> None:
        time_str = CountdownManager.format_time(seconds)
        self.countdown_label.setText(time_str)
        if seconds <= 60:
            self.countdown_label.setStyleSheet("color: #F44336;")
        elif seconds <= 300:
            self.countdown_label.setStyleSheet("color: #FF9800;")
        else:
            self.countdown_label.setStyleSheet("color: #2196F3;")
    
    def _on_countdown_finished(self) -> None:
        self._log("倒计时结束，开始执行...")
        self._update_button_states(running=False)
        QTimer.singleShot(100, self._execute_automation)
    
    def _on_countdown_status_changed(self, status: str) -> None:
        self.status_label.setText(status)
    
    def _on_executor_state_changed(self, state: ExecutionState, description: str) -> None:
        self.status_label.setText(description)
        if state == ExecutionState.COMPLETED:
            self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        elif state == ExecutionState.FAILED:
            self.status_label.setStyleSheet("font-weight: bold; color: #F44336;")
        else:
            self.status_label.setStyleSheet("font-weight: bold; color: #2196F3;")
    
    def _on_executor_progress_updated(self, current: int, total: int, description: str) -> None:
        self.progress_bar.setValue(current)
        self.progress_bar.setFormat(f"{description} (%v/%m)")
    
    def _on_log_message(self, message: str) -> None:
        self._log(message)
    
    def _on_executor_error(self, error: str) -> None:
        self._log(f"错误: {error}")
    
    def _on_execution_completed(self, success: bool) -> None:
        if success:
            self._log("执行成功!")
        else:
            self._log("执行失败!")
        self._update_button_states(running=False)
    
    def _update_button_states(self, running: bool) -> None:
        self.start_btn.setEnabled(not running)
        self.pause_btn.setEnabled(running)
        if not running:
            self.pause_btn.setText("⏸ 暂停")
    
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
        
        rdp_window_titles = {
            "MobaXterm": "MobaXterm",
            "Xshell": "Xshell",
            "Windows远程桌面": "远程桌面连接",
            "自定义": self.custom_rdp_input.text().strip()
        }
        rdp_title = rdp_window_titles.get(self.rdp_combo.currentText(), "")
        
        config = ExecutionConfig(
            target_program_path=full_path,
            rdp_window_title=rdp_title,
            rdp_reconnect_attempts=3,
            rdp_reconnect_delay=5.0,
            wake_attempts=3,
            wake_delay=2.0,
            click_delay=1.0
        )
        self._log(f"RDP软件: {self.rdp_combo.currentText()}")
        if rdp_title:
            self._log(f"窗口标题: {rdp_title}")
        self._log(f"目标程序: {full_path}")
        self._executor.set_config(config)
        self._executor.execute()
    
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
                padding: 6px 12px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:pressed { background-color: #0D47A1; }
            QPushButton:disabled { background-color: #BDBDBD; }
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 4px;
                text-align: center;
                background-color: #E0E0E0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fafafa;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            QLineEdit:focus { border-color: #2196F3; }
        """)
