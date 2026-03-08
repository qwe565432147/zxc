"""
截图工具模块
============

提供截图功能，用于创建模板图片。
"""

import time
from pathlib import Path
from typing import Optional, Tuple, List

import cv2
import numpy as np
from PIL import Image, ImageGrab
from PySide6.QtWidgets import (
    QWidget, QApplication, QMessageBox, QListWidgetItem,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox, 
    QListWidget, QComboBox, QSpacerItem, QSizePolicy, QDialog, QLineEdit
)
from PySide6.QtCore import Qt, QRect, Signal, QPoint, QTimer
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QGuiApplication

from .runtime import TEMPLATES_DIR


class ScreenshotTool:
    """截图工具类"""
    
    def __init__(self, templates_dir: str = None):
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = TEMPLATES_DIR
        self.templates_dir.mkdir(parents=True, exist_ok=True)
    
    def capture_region(self, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    
    def save_template(self, image: np.ndarray, name: str) -> Path:
        filepath = self.templates_dir / f"{name}.png"
        cv2.imwrite(str(filepath), image)
        return filepath
    
    def template_exists(self, name: str) -> bool:
        return (self.templates_dir / f"{name}.png").exists()


class RegionSelector(QWidget):
    """区域选择器 - 全屏半透明窗口"""
    
    region_selected = Signal(int, int, int, int)
    selection_cancelled = Signal()
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        self._selecting = False
        self._start_pos = None
        self._end_pos = None
        self._screen_geometry = None
        self._init_screen_geometry()
    
    def _init_screen_geometry(self):
        screens = QGuiApplication.screens()
        if screens:
            total_rect = screens[0].geometry()
            for screen in screens[1:]:
                total_rect = total_rect.united(screen.geometry())
            self._screen_geometry = total_rect
        else:
            self._screen_geometry = QRect(0, 0, 1920, 1080)
    
    def showEvent(self, event):
        self.setGeometry(self._screen_geometry)
        super().showEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))
        
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignTop | Qt.AlignHCenter, 
                        "拖拽鼠标选择区域 | ESC 取消")
        
        if self._start_pos and self._end_pos:
            rect = QRect(self._start_pos, self._end_pos).normalized()
            painter.fillRect(rect, QColor(0, 0, 0, 0))
            pen = QPen(QColor(0, 200, 255), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
            painter.drawText(rect.bottomRight() + QPoint(5, 15), 
                           f"{rect.width()} x {rect.height()}")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._selecting = True
            self._start_pos = event.pos()
            self._end_pos = event.pos()
            self.update()
    
    def mouseMoveEvent(self, event):
        if self._selecting:
            self._end_pos = event.pos()
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._selecting:
            self._selecting = False
            if self._start_pos and self._end_pos:
                rect = QRect(self._start_pos, self._end_pos).normalized()
                if rect.width() > 10 and rect.height() > 10:
                    self.region_selected.emit(
                        rect.left(), rect.top(),
                        rect.right(), rect.bottom()
                    )
                    self.close()
                    return
            self.close()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.selection_cancelled.emit()
            self.close()


class TemplateCaptureWizard(QDialog):
    """模板配置向导 - 独立对话框"""
    
    RDP_SOFTWARES = {
        "MobaXterm": {
            "window_title": "MobaXterm",
            "templates": [
                ("rdp_connected", "RDP已连接状态", "RDP正常连接时的特征区域"),
                ("rdp_disconnected", "RDP断开连接状态", "RDP断开时的提示区域"),
                ("rdp_reconnect_button", "RDP重连按钮", "RDP断开时的重连按钮"),
                ("rdp_sleeping", "RDP休眠状态", "远程电脑休眠时的特征区域"),
            ]
        },
        "Xshell": {
            "window_title": "Xshell",
            "templates": [
                ("rdp_connected", "SSH已连接状态", "SSH正常连接时的特征区域"),
                ("rdp_disconnected", "SSH断开连接状态", "SSH断开时的提示区域"),
                ("rdp_reconnect_button", "重连按钮", "断开时的重连按钮"),
                ("rdp_sleeping", "远程休眠状态", "远程休眠时的特征区域"),
            ]
        },
        "Windows远程桌面": {
            "window_title": "远程桌面连接",
            "templates": [
                ("rdp_connected", "RDP已连接状态", "RDP正常连接时的特征区域"),
                ("rdp_disconnected", "RDP断开连接状态", "RDP断开时的提示区域"),
                ("rdp_reconnect_button", "重连按钮", "断开时的重连按钮"),
                ("rdp_sleeping", "远程休眠状态", "远程休眠时的特征区域"),
            ]
        },
        "自定义RDP软件": {
            "window_title": "",
            "templates": [
                ("rdp_connected", "已连接状态", "正常连接时的特征区域"),
                ("rdp_disconnected", "断开连接状态", "断开时的提示区域"),
                ("rdp_reconnect_button", "重连按钮", "断开时的重连按钮"),
                ("rdp_sleeping", "休眠状态", "休眠时的特征区域"),
            ]
        }
    }
    
    capture_completed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._screenshot_tool = ScreenshotTool()
        self._current_index = 0
        self._selector = None
        self._current_software = "MobaXterm"
        self._init_ui()
    
    def _init_ui(self):
        self.setWindowTitle("模板配置向导")
        self.setMinimumSize(520, 520)
        self.resize(560, 560)
        self.setModal(False)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("RDP状态识别模板配置")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1976D2;")
        layout.addWidget(title)
        
        rdp_group = QGroupBox("选择RDP软件")
        rdp_layout = QVBoxLayout(rdp_group)
        
        rdp_select_layout = QHBoxLayout()
        rdp_select_layout.addWidget(QLabel("RDP软件:"))
        self.rdp_combo = QComboBox()
        self.rdp_combo.addItems(list(self.RDP_SOFTWARES.keys()))
        self.rdp_combo.currentTextChanged.connect(self._on_rdp_changed)
        rdp_select_layout.addWidget(self.rdp_combo)
        rdp_select_layout.addStretch()
        rdp_layout.addLayout(rdp_select_layout)
        
        title_layout = QHBoxLayout()
        title_layout.addWidget(QLabel("窗口标题:"))
        self.window_title_input = QLineEdit()
        self.window_title_input.setPlaceholderText("输入RDP软件窗口标题")
        self.window_title_input.setText("MobaXterm")
        title_layout.addWidget(self.window_title_input)
        rdp_layout.addLayout(title_layout)
        
        layout.addWidget(rdp_group)
        
        info_group = QGroupBox("说明")
        info_layout = QVBoxLayout(info_group)
        info_label = QLabel(
            "此向导引导您截取RDP状态识别所需的模板图片。\n"
            "请确保在正确的RDP状态下截取对应模板。\n"
            "✓ 表示已截取，○ 表示未截取"
        )
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        layout.addWidget(info_group)
        
        list_group = QGroupBox("模板列表")
        list_layout = QVBoxLayout(list_group)
        
        self.template_list = QListWidget()
        self.template_list.setMinimumHeight(140)
        list_layout.addWidget(self.template_list)
        layout.addWidget(list_group)
        
        self.desc_label = QLabel("选择模板查看说明")
        self.desc_label.setWordWrap(True)
        self.desc_label.setMinimumHeight(50)
        self.desc_label.setStyleSheet(
            "padding: 10px; background-color: #E3F2FD; border-radius: 4px;"
        )
        layout.addWidget(self.desc_label)
        
        btn_layout = QHBoxLayout()
        
        self.capture_btn = QPushButton("截取选中")
        self.capture_btn.setFixedHeight(36)
        self.capture_btn.clicked.connect(self._on_capture_clicked)
        btn_layout.addWidget(self.capture_btn)
        
        self.capture_all_btn = QPushButton("依次截取全部")
        self.capture_all_btn.setFixedHeight(36)
        self.capture_all_btn.clicked.connect(self._on_capture_all_clicked)
        btn_layout.addWidget(self.capture_all_btn)
        
        layout.addLayout(btn_layout)
        
        close_btn = QPushButton("关闭")
        close_btn.setFixedHeight(36)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.template_list.currentRowChanged.connect(self._on_selection_changed)
        self._refresh_template_list()
    
    def _on_rdp_changed(self, software: str):
        self._current_software = software
        config = self.RDP_SOFTWARES.get(software, {})
        window_title = config.get("window_title", "")
        self.window_title_input.setText(window_title)
        self._refresh_template_list()
    
    def _refresh_template_list(self):
        self.template_list.clear()
        config = self.RDP_SOFTWARES.get(self._current_software, {})
        templates = config.get("templates", [])
        
        for name, display_name, description in templates:
            item = QListWidgetItem()
            self._update_item_status(item, name, display_name)
            item.setData(Qt.UserRole, (name, display_name, description))
            self.template_list.addItem(item)
        
        if self.template_list.count() > 0:
            self.template_list.setCurrentRow(0)
    
    def _update_item_status(self, item: QListWidgetItem, name: str, display_name: str):
        exists = self._screenshot_tool.template_exists(name)
        if exists:
            item.setText(f"✓ {display_name}")
            item.setForeground(QColor(76, 175, 80))
        else:
            item.setText(f"○ {display_name}")
            item.setForeground(QColor(120, 120, 120))
    
    def _on_selection_changed(self, row: int):
        config = self.RDP_SOFTWARES.get(self._current_software, {})
        templates = config.get("templates", [])
        
        if 0 <= row < len(templates):
            name, display_name, description = templates[row]
            exists = self._screenshot_tool.template_exists(name)
            status = "✓ 已存在" if exists else "○ 未截取"
            self.desc_label.setText(f"【{display_name}】{status}\n{description}")
    
    def _on_capture_clicked(self):
        row = self.template_list.currentRow()
        if 0 <= row < self.template_list.count():
            self._capture_template(row)
    
    def _on_capture_all_clicked(self):
        self._current_index = 0
        self._capture_next_template()
    
    def _capture_next_template(self):
        config = self.RDP_SOFTWARES.get(self._current_software, {})
        templates = config.get("templates", [])
        
        if self._current_index < len(templates):
            self.template_list.setCurrentRow(self._current_index)
            self._capture_template(self._current_index)
        else:
            QMessageBox.information(self, "完成", "所有模板截取完成！")
            self.capture_completed.emit()
    
    def _capture_template(self, index: int):
        config = self.RDP_SOFTWARES.get(self._current_software, {})
        templates = config.get("templates", [])
        
        if not (0 <= index < len(templates)):
            return
        
        name, display_name, description = templates[index]
        
        ret = QMessageBox.information(
            self, 
            f"截取: {display_name}",
            f"{description}\n\n点击确定后拖拽选择截图区域",
            QMessageBox.Ok | QMessageBox.Cancel
        )
        
        if ret != QMessageBox.Ok:
            return
        
        self._current_index = index
        self.hide()
        QTimer.singleShot(200, self._start_selector)
    
    def _start_selector(self):
        if self._selector:
            self._selector.close()
            self._selector = None
        
        self._selector = RegionSelector()
        self._selector.region_selected.connect(self._on_region_selected)
        self._selector.selection_cancelled.connect(self._on_selection_cancelled)
        self._selector.show()
    
    def _on_region_selected(self, x1: int, y1: int, x2: int, y2: int):
        if self._selector:
            self._selector.close()
            self._selector = None
        
        config = self.RDP_SOFTWARES.get(self._current_software, {})
        templates = config.get("templates", [])
        name, display_name, _ = templates[self._current_index]
        
        image = self._screenshot_tool.capture_region(x1, y1, x2, y2)
        filepath = self._screenshot_tool.save_template(image, name)
        
        item = self.template_list.item(self._current_index)
        self._update_item_status(item, name, display_name)
        
        self.show()
        
        QMessageBox.information(self, "保存成功", f"模板已保存:\n{filepath}")
        
        if self._current_index < len(templates) - 1:
            self._current_index += 1
            ret = QMessageBox.question(
                self, "继续", "是否继续截取下一个模板？",
                QMessageBox.Yes | QMessageBox.No
            )
            if ret == QMessageBox.Yes:
                self._capture_next_template()
    
    def _on_selection_cancelled(self):
        if self._selector:
            self._selector = None
        self.show()
    
    def closeEvent(self, event):
        if self._selector:
            self._selector.close()
            self._selector = None
        super().closeEvent(event)
    
    def get_current_rdp_config(self) -> dict:
        config = self.RDP_SOFTWARES.get(self._current_software, {}).copy()
        config["window_title"] = self.window_title_input.text().strip()
        return config
