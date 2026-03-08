"""
窗口绑定控件模块
================

提供拖拽绑定窗口的UI控件。
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QDialog, 
    QTextEdit, QPushButton, QComboBox, QFrame, QSizePolicy,
    QDialogButtonBox, QTabWidget, QTreeWidget, QTreeWidgetItem,
    QGroupBox, QApplication, QStyle, QStyleOptionComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QPoint, QSize, QRect
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QCursor, QFont, QPixmap

import win32gui
import win32api
import win32process
import win32con
import ctypes


class WindowHighlighter(QWidget):
    """窗口高亮边框"""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self._flash_state = False
        self._flash_timer = QTimer()
        self._flash_timer.timeout.connect(self._toggle_flash)
        self._target_hwnd = None
        self._flash_count = 0
        self._max_flashes = 6
    
    def start_highlight(self, hwnd: int, continuous: bool = False):
        """开始高亮指定窗口"""
        self._target_hwnd = hwnd
        self._continuous = continuous
        self._flash_count = 0
        self._update_geometry()
        self._flash_state = True
        self._flash_timer.start(250)
        self.show()
    
    def stop_highlight(self):
        """停止高亮"""
        self._flash_timer.stop()
        self.hide()
        self._target_hwnd = None
    
    def _update_geometry(self):
        """更新位置到目标窗口内部"""
        if not self._target_hwnd:
            return
        try:
            rect = win32gui.GetWindowRect(self._target_hwnd)
            inset = 6
            self.setGeometry(
                rect[0] + inset, 
                rect[1] + inset, 
                rect[2] - rect[0] - inset * 2, 
                rect[3] - rect[1] - inset * 2
            )
        except Exception:
            pass
    
    def _toggle_flash(self):
        """切换闪烁状态"""
        self._flash_state = not self._flash_state
        self._flash_count += 1
        
        if not self._continuous and self._flash_count >= self._max_flashes:
            self.stop_highlight()
            return
        
        self._update_geometry()
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self._flash_state:
            color = QColor(255, 87, 34)
        else:
            color = QColor(255, 193, 7)
        
        pen = QPen(color, 4)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.rect().adjusted(2, 2, -2, -2))


class DraggingCrosshair(QWidget):
    """拖拽时跟随鼠标的准星窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setFixedSize(32, 32)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setBrush(QBrush(QColor(255, 243, 224)))
        painter.setPen(QPen(QColor(255, 87, 34), 2))
        painter.drawRoundedRect(1, 1, self.width() - 2, self.height() - 2, 4, 4)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        pen = QPen(QColor(255, 87, 34), 2, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        
        painter.drawLine(center_x - 10, center_y, center_x - 4, center_y)
        painter.drawLine(center_x + 4, center_y, center_x + 10, center_y)
        painter.drawLine(center_x, center_y - 10, center_x, center_y - 4)
        painter.drawLine(center_x, center_y + 4, center_x, center_y + 10)
        
        painter.setBrush(QBrush(QColor(255, 87, 34)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(center_x, center_y), 2, 2)
    
    def move_to_cursor(self):
        """移动到鼠标位置"""
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() - self.width() // 2, cursor_pos.y() - self.height() // 2)


class ArrowComboBox(QComboBox):
    """带自定义箭头的下拉框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(180)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet("""
            QComboBox::drop-down { width: 0; }
            QComboBox::down-arrow { image: none; }
        """)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        btn_width = 24
        btn_rect = QRect(self.width() - btn_width - 2, 2, btn_width - 2, self.height() - 4)
        
        painter.setPen(QPen(QColor("#E0E0E0"), 1))
        painter.drawLine(self.width() - btn_width - 2, 4, self.width() - btn_width - 2, self.height() - 4)
        
        center_x = btn_rect.center().x()
        center_y = btn_rect.center().y()
        
        painter.setPen(QPen(QColor("#666666"), 2, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(center_x - 4, center_y - 2, center_x, center_y + 2)
        painter.drawLine(center_x, center_y + 2, center_x + 4, center_y - 2)


class CrosshairIcon(QWidget):
    """准星图标控件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 44)
        self._hover = False
        self._dragging = False
    
    def set_hover(self, hover: bool):
        self._hover = hover
        self.update()
    
    def set_dragging(self, dragging: bool):
        self._dragging = dragging
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self._dragging:
            bg_color = QColor(255, 243, 224)
            border_color = QColor(255, 152, 0)
            cross_color = QColor(255, 87, 34)
        elif self._hover:
            bg_color = QColor(227, 242, 253)
            border_color = QColor(33, 150, 243)
            cross_color = QColor(25, 118, 210)
        else:
            bg_color = QColor(245, 245, 245)
            border_color = QColor(189, 189, 189)
            cross_color = QColor(117, 117, 117)
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(border_color, 2))
        painter.drawRoundedRect(2, 2, self.width() - 4, self.height() - 4, 6, 6)
        
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        pen = QPen(cross_color, 2.5, Qt.SolidLine, Qt.RoundCap)
        painter.setPen(pen)
        
        painter.drawLine(center_x - 12, center_y, center_x - 5, center_y)
        painter.drawLine(center_x + 5, center_y, center_x + 12, center_y)
        painter.drawLine(center_x, center_y - 12, center_x, center_y - 5)
        painter.drawLine(center_x, center_y + 5, center_x, center_y + 12)
        
        painter.setBrush(QBrush(cross_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPoint(center_x, center_y), 3, 3)
        
        pen = QPen(cross_color, 1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPoint(center_x, center_y), 8, 8)
    
    def enterEvent(self, event):
        self.set_hover(True)
    
    def leaveEvent(self, event):
        self.set_hover(False)


class WindowDetailDialog(QDialog):
    """窗口详情对话框 - WinSpy++风格"""
    
    WINDOW_STYLES = {
        win32con.WS_OVERLAPPED: "WS_OVERLAPPED",
        win32con.WS_POPUP: "WS_POPUP",
        win32con.WS_CHILD: "WS_CHILD",
        win32con.WS_MINIMIZE: "WS_MINIMIZE",
        win32con.WS_VISIBLE: "WS_VISIBLE",
        win32con.WS_DISABLED: "WS_DISABLED",
        win32con.WS_CLIPSIBLINGS: "WS_CLIPSIBLINGS",
        win32con.WS_CLIPCHILDREN: "WS_CLIPCHILDREN",
        win32con.WS_MAXIMIZE: "WS_MAXIMIZE",
        win32con.WS_BORDER: "WS_BORDER",
        win32con.WS_DLGFRAME: "WS_DLGFRAME",
        win32con.WS_VSCROLL: "WS_VSCROLL",
        win32con.WS_HSCROLL: "WS_HSCROLL",
        win32con.WS_SYSMENU: "WS_SYSMENU",
        win32con.WS_THICKFRAME: "WS_THICKFRAME",
        win32con.WS_GROUP: "WS_GROUP",
        win32con.WS_TABSTOP: "WS_TABSTOP",
        win32con.WS_MINIMIZEBOX: "WS_MINIMIZEBOX",
        win32con.WS_MAXIMIZEBOX: "WS_MAXIMIZEBOX",
    }
    
    EXTENDED_STYLES = {
        win32con.WS_EX_DLGMODALFRAME: "WS_EX_DLGMODALFRAME",
        win32con.WS_EX_NOPARENTNOTIFY: "WS_EX_NOPARENTNOTIFY",
        win32con.WS_EX_TOPMOST: "WS_EX_TOPMOST",
        win32con.WS_EX_ACCEPTFILES: "WS_EX_ACCEPTFILES",
        win32con.WS_EX_TRANSPARENT: "WS_EX_TRANSPARENT",
        win32con.WS_EX_MDICHILD: "WS_EX_MDICHILD",
        win32con.WS_EX_TOOLWINDOW: "WS_EX_TOOLWINDOW",
        win32con.WS_EX_WINDOWEDGE: "WS_EX_WINDOWEDGE",
        win32con.WS_EX_CLIENTEDGE: "WS_EX_CLIENTEDGE",
        win32con.WS_EX_CONTEXTHELP: "WS_EX_CONTEXTHELP",
        win32con.WS_EX_RIGHT: "WS_EX_RIGHT",
        win32con.WS_EX_RTLREADING: "WS_EX_RTLREADING",
        win32con.WS_EX_LEFTSCROLLBAR: "WS_EX_LEFTSCROLLBAR",
        win32con.WS_EX_CONTROLPARENT: "WS_EX_CONTROLPARENT",
        win32con.WS_EX_STATICEDGE: "WS_EX_STATICEDGE",
        win32con.WS_EX_APPWINDOW: "WS_EX_APPWINDOW",
        win32con.WS_EX_LAYERED: "WS_EX_LAYERED",
        win32con.WS_EX_NOINHERITLAYOUT: "WS_EX_NOINHERITLAYOUT",
        win32con.WS_EX_LAYOUTRTL: "WS_EX_LAYOUTRTL",
        win32con.WS_EX_COMPOSITED: "WS_EX_COMPOSITED",
        win32con.WS_EX_NOACTIVATE: "WS_EX_NOACTIVATE",
    }
    
    def __init__(self, window_info: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("窗口详情 - WinSpy风格")
        self.setMinimumSize(650, 600)
        self._window_info = window_info
        self._hwnd = window_info.get('hwnd')
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        tab_widget = QTabWidget()
        
        tab_widget.addTab(self._create_general_tab(), "常规")
        tab_widget.addTab(self._create_styles_tab(), "样式")
        tab_widget.addTab(self._create_process_tab(), "进程")
        tab_widget.addTab(self._create_hierarchy_tab(), "层级")
        tab_widget.addTab(self._create_properties_tab(), "属性")
        tab_widget.addTab(self._create_class_tab(), "类信息")
        
        layout.addWidget(tab_widget)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
    
    def _create_general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(self._create_group("窗口基本信息", self._get_basic_info()))
        layout.addWidget(self._create_group("位置与尺寸", self._get_position_info()))
        layout.addWidget(self._create_group("窗口状态", self._get_state_info()))
        layout.addStretch()
        
        return widget
    
    def _create_styles_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(self._create_group("窗口样式 (Window Styles)", self._get_window_styles()))
        layout.addWidget(self._create_group("扩展样式 (Extended Styles)", self._get_extended_styles()))
        layout.addWidget(self._create_group("类样式 (Class Styles)", self._get_class_styles()))
        layout.addStretch()
        
        return widget
    
    def _create_process_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(self._create_group("进程信息", self._get_process_info()))
        layout.addWidget(self._create_group("线程信息", self._get_thread_info()))
        layout.addWidget(self._create_group("模块信息", self._get_module_info()))
        layout.addStretch()
        
        return widget
    
    def _create_hierarchy_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(self._create_group("窗口层级", self._get_hierarchy_info()))
        layout.addWidget(self._create_group("子窗口列表", self._get_children_info()))
        layout.addWidget(self._create_group("兄弟窗口", self._get_siblings_info()))
        layout.addStretch()
        
        return widget
    
    def _create_properties_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        tree = QTreeWidget()
        tree.setHeaderLabels(["属性", "值"])
        tree.setColumnWidth(0, 200)
        
        props = self._get_all_properties()
        for category, items in props.items():
            category_item = QTreeWidgetItem([category, ""])
            font = QFont()
            font.setBold(True)
            category_item.setFont(0, font)
            tree.addTopLevelItem(category_item)
            
            for prop_name, prop_value in items.items():
                item = QTreeWidgetItem([prop_name, str(prop_value)])
                category_item.addChild(item)
            
            category_item.setExpanded(True)
        
        layout.addWidget(tree)
        return widget
    
    def _create_class_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(self._create_group("窗口类信息", self._get_class_info()))
        layout.addWidget(self._create_group("窗口类样式", self._get_class_style_info()))
        layout.addStretch()
        
        return widget
    
    def _create_group(self, title: str, content: str) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))
        text_edit.setText(content)
        text_edit.setMaximumHeight(200)
        
        layout.addWidget(text_edit)
        return group
    
    def _safe_call(self, func, default="获取失败"):
        try:
            return func()
        except Exception:
            return default
    
    def _get_basic_info(self) -> str:
        hwnd = self._hwnd
        title = self._window_info.get('title', '未知')
        class_name = self._window_info.get('class_name', '未知')
        
        parent_hwnd = self._safe_call(lambda: win32gui.GetParent(hwnd), 0)
        owner_hwnd = self._safe_call(lambda: win32gui.GetWindow(hwnd, win32con.GW_OWNER), 0)
        
        instance = self._safe_call(lambda: win32gui.GetWindowLong(hwnd, win32con.GWL_HINSTANCE), 0)
        id_value = self._safe_call(lambda: win32gui.GetWindowLong(hwnd, win32con.GWL_ID), 0)
        userdata = self._safe_call(lambda: win32gui.GetWindowLong(hwnd, win32con.GWL_USERDATA), 0)
        wndproc = self._safe_call(lambda: win32gui.GetWindowLong(hwnd, win32con.GWL_WNDPROC), 0)
        
        return f"""窗口句柄: {hwnd} (0x{hwnd:08X})
窗口标题: {title}
窗口类名: {class_name}
父窗口句柄: {parent_hwnd} (0x{parent_hwnd:08X})
所有者窗口: {owner_hwnd} (0x{owner_hwnd:08X})
实例句柄: {instance} (0x{instance:08X})
窗口ID: {id_value}
用户数据: {userdata}
窗口过程: {wndproc} (0x{wndproc:08X})"""
    
    def _get_position_info(self) -> str:
        hwnd = self._hwnd
        rect = self._window_info.get('rect', (0, 0, 0, 0))
        width = self._window_info.get('width', 0)
        height = self._window_info.get('height', 0)
        
        client_rect = self._safe_call(lambda: win32gui.GetClientRect(hwnd), (0, 0, 0, 0))
        client_width = client_rect[2] - client_rect[0]
        client_height = client_rect[3] - client_rect[1]
        
        window_rect = self._safe_call(lambda: win32gui.GetWindowRect(hwnd), (0, 0, 0, 0))
        
        return f"""窗口矩形:
  左上角: ({rect[0]}, {rect[1]})
  右下角: ({rect[2]}, {rect[3]})
  宽度: {width} 像素
  高度: {height} 像素

客户区矩形:
  左上角: ({client_rect[0]}, {client_rect[1]})
  右下角: ({client_rect[2]}, {client_rect[3]})
  宽度: {client_width} 像素
  高度: {client_height} 像素

边框宽度: {(width - client_width) // 2} 像素
标题栏高度: {height - client_height - ((width - client_width) // 2) * 2} 像素"""
    
    def _get_state_info(self) -> str:
        hwnd = self._hwnd
        
        is_visible = self._safe_call(lambda: win32gui.IsWindowVisible(hwnd), False)
        is_enabled = self._safe_call(lambda: win32gui.IsWindowEnabled(hwnd), False)
        is_zoomed = self._safe_call(lambda: win32gui.IsZoomed(hwnd), False)
        is_iconic = self._safe_call(lambda: win32gui.IsIconic(hwnd), False)
        
        try:
            foreground_hwnd = win32gui.GetForegroundWindow()
            is_foreground = (foreground_hwnd == hwnd)
        except Exception:
            is_foreground = False
        
        style = self._safe_call(lambda: win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE), 0)
        
        state_list = []
        if is_iconic:
            state_list.append("最小化")
        elif is_zoomed:
            state_list.append("最大化")
        elif is_visible:
            state_list.append("正常显示")
        else:
            state_list.append("隐藏")
        
        if style & win32con.WS_DISABLED:
            state_list.append("禁用")
        
        state_str = " / ".join(state_list) if state_list else "未知"
        
        return f"""可见性: {'是' if is_visible else '否'}
启用状态: {'是' if is_enabled else '否'}
最大化: {'是' if is_zoomed else '否'}
最小化: {'是' if is_iconic else '否'}
前台窗口: {'是' if is_foreground else '否'}
显示状态: {state_str}"""
    
    def _get_window_styles(self) -> str:
        hwnd = self._hwnd
        
        style = self._safe_call(lambda: win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE), 0)
        style_hex = f"0x{style:08X}"
        
        style_list = []
        for flag, name in sorted(self.WINDOW_STYLES.items()):
            if style & flag:
                style_list.append(f"  {name}")
        
        styles_str = "\n".join(style_list) if style_list else "  无"
        
        return f"""样式值: {style_hex} ({style})

包含样式:
{styles_str}"""
    
    def _get_extended_styles(self) -> str:
        hwnd = self._hwnd
        
        ex_style = self._safe_call(lambda: win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE), 0)
        style_hex = f"0x{ex_style:08X}"
        
        style_list = []
        for flag, name in sorted(self.EXTENDED_STYLES.items()):
            if ex_style & flag:
                style_list.append(f"  {name}")
        
        styles_str = "\n".join(style_list) if style_list else "  无"
        
        return f"""扩展样式值: {style_hex} ({ex_style})

包含样式:
{styles_str}"""
    
    def _get_class_styles(self) -> str:
        hwnd = self._hwnd
        
        try:
            class_style = win32gui.GetClassLong(hwnd, win32con.GCL_STYLE)
            style_hex = f"0x{class_style:08X}"
            
            class_styles = {
                win32con.CS_VREDRAW: "CS_VREDRAW",
                win32con.CS_HREDRAW: "CS_HREDRAW",
                win32con.CS_DBLCLKS: "CS_DBLCLKS",
                win32con.CS_OWNDC: "CS_OWNDC",
                win32con.CS_CLASSDC: "CS_CLASSDC",
                win32con.CS_PARENTDC: "CS_PARENTDC",
                win32con.CS_NOCLOSE: "CS_NOCLOSE",
                win32con.CS_SAVEBITS: "CS_SAVEBITS",
                win32con.CS_BYTEALIGNCLIENT: "CS_BYTEALIGNCLIENT",
                win32con.CS_BYTEALIGNWINDOW: "CS_BYTEALIGNWINDOW",
                win32con.CS_GLOBALCLASS: "CS_GLOBALCLASS",
            }
            
            style_list = []
            for flag, name in sorted(class_styles.items()):
                if class_style & flag:
                    style_list.append(f"  {name}")
            
            styles_str = "\n".join(style_list) if style_list else "  无"
            
            return f"""类样式值: {style_hex} ({class_style})

包含样式:
{styles_str}"""
        except Exception:
            return "获取失败"
    
    def _get_process_info(self) -> str:
        hwnd = self._hwnd
        process_id = self._window_info.get('process_id', 0)
        
        try:
            kernel32 = ctypes.windll.kernel32
            psapi = ctypes.windll.psapi
            
            h_process = kernel32.OpenProcess(0x0410, False, process_id)
            if h_process:
                exe_path = ctypes.create_unicode_buffer(260)
                kernel32.GetModuleFileNameExW(h_process, None, exe_path, 260)
                
                memory_info = ctypes.c_ulonglong()
                psapi.GetProcessMemoryInfo(h_process, ctypes.byref(memory_info), ctypes.sizeof(memory_info))
                
                kernel32.CloseHandle(h_process)
                process_name = exe_path.value
            else:
                process_name = "无法获取"
        except Exception:
            process_name = "获取失败"
        
        return f"""进程ID: {process_id}
进程路径: {process_name}"""
    
    def _get_thread_info(self) -> str:
        hwnd = self._hwnd
        
        thread_id, process_id = self._safe_call(
            lambda: win32process.GetWindowThreadProcessId(hwnd), 
            (0, 0)
        )
        
        try:
            foreground_thread = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[0]
            is_foreground_thread = (thread_id == foreground_thread)
        except Exception:
            is_foreground_thread = False
        
        return f"""线程ID: {thread_id}
所属进程ID: {process_id}
是否前台线程: {'是' if is_foreground_thread else '否'}"""
    
    def _get_module_info(self) -> str:
        hwnd = self._hwnd
        
        instance = self._safe_call(lambda: win32gui.GetWindowLong(hwnd, win32con.GWL_HINSTANCE), 0)
        
        try:
            kernel32 = ctypes.windll.kernel32
            module_name = ctypes.create_unicode_buffer(260)
            kernel32.GetModuleFileNameW(instance, module_name, 260)
            module_path = module_name.value
        except Exception:
            module_path = "获取失败"
        
        return f"""实例句柄: {instance} (0x{instance:08X})
模块路径: {module_path}"""
    
    def _get_hierarchy_info(self) -> str:
        hwnd = self._hwnd
        
        parent = self._safe_call(lambda: win32gui.GetParent(hwnd), 0)
        owner = self._safe_call(lambda: win32gui.GetWindow(hwnd, win32con.GW_OWNER), 0)
        first_child = self._safe_call(lambda: win32gui.GetWindow(hwnd, win32con.GW_CHILD), 0)
        next_sibling = self._safe_call(lambda: win32gui.GetWindow(hwnd, win32con.GW_HWNDNEXT), 0)
        prev_sibling = self._safe_call(lambda: win32gui.GetWindow(hwnd, win32con.GW_HWNDPREV), 0)
        first_visible = self._safe_call(lambda: win32gui.GetWindow(hwnd, win32con.GW_HWNDFIRST), 0)
        last_visible = self._safe_call(lambda: win32gui.GetWindow(hwnd, win32con.GW_HWNDLAST), 0)
        
        def get_title(h):
            if h == 0:
                return "(无)"
            try:
                t = win32gui.GetWindowText(h)
                return f"{t[:20]}..." if len(t) > 20 else t
            except Exception:
                return "(无法获取)"
        
        return f"""父窗口: {parent} (0x{parent:08X}) - {get_title(parent)}
所有者窗口: {owner} (0x{owner:08X}) - {get_title(owner)}
第一个子窗口: {first_child} (0x{first_child:08X}) - {get_title(first_child)}
下一个兄弟: {next_sibling} (0x{next_sibling:08X}) - {get_title(next_sibling)}
上一个兄弟: {prev_sibling} (0x{prev_sibling:08X}) - {get_title(prev_sibling)}
第一个可见窗口: {first_visible} (0x{first_visible:08X})
最后一个可见窗口: {last_visible} (0x{last_visible:08X})"""
    
    def _get_children_info(self) -> str:
        hwnd = self._hwnd
        
        children = []
        child = self._safe_call(lambda: win32gui.GetWindow(hwnd, win32con.GW_CHILD), 0)
        
        while child and child != 0:
            try:
                child_title = win32gui.GetWindowText(child)
                child_class = win32gui.GetClassName(child)
                children.append(f"  {child} (0x{child:08X}) - {child_class}: {child_title[:30]}")
            except Exception:
                children.append(f"  {child} (0x{child:08X})")
            
            child = self._safe_call(lambda: win32gui.GetWindow(child, win32con.GW_HWNDNEXT), 0)
        
        if not children:
            return "无子窗口"
        
        return f"子窗口数量: {len(children)}\n\n" + "\n".join(children[:20]) + ("\n  ..." if len(children) > 20 else "")
    
    def _get_siblings_info(self) -> str:
        hwnd = self._hwnd
        
        siblings = []
        
        prev = hwnd
        while True:
            prev = self._safe_call(lambda: win32gui.GetWindow(prev, win32con.GW_HWNDPREV), 0)
            if prev == 0 or prev == hwnd:
                break
            try:
                title = win32gui.GetWindowText(prev)
                siblings.insert(0, f"  {prev} (0x{prev:08X}) - {title[:30]}")
            except Exception:
                siblings.insert(0, f"  {prev} (0x{prev:08X})")
        
        siblings.append(f"  {hwnd} (0x{hwnd:08X}) - 当前窗口 <<<")
        
        next_hwnd = hwnd
        while True:
            next_hwnd = self._safe_call(lambda: win32gui.GetWindow(next_hwnd, win32con.GW_HWNDNEXT), 0)
            if next_hwnd == 0 or next_hwnd == hwnd:
                break
            try:
                title = win32gui.GetWindowText(next_hwnd)
                siblings.append(f"  {next_hwnd} (0x{next_hwnd:08X}) - {title[:30]}")
            except Exception:
                siblings.append(f"  {next_hwnd} (0x{next_hwnd:08X})")
        
        return f"兄弟窗口列表:\n" + "\n".join(siblings[:15]) + ("\n  ..." if len(siblings) > 15 else "")
    
    def _get_class_info(self) -> str:
        hwnd = self._hwnd
        class_name = self._window_info.get('class_name', '未知')
        
        try:
            class_atom = win32gui.GetClassLong(hwnd, win32con.GCW_ATOM)
            class_style = win32gui.GetClassLong(hwnd, win32con.GCL_STYLE)
            class_cbWndExtra = win32gui.GetClassLong(hwnd, win32con.GCL_CBWNDEXTRA)
            class_cbClsExtra = win32gui.GetClassLong(hwnd, win32con.GCL_CBCLSEXTRA)
            class_hInstance = win32gui.GetClassLong(hwnd, win32con.GCL_HMODULE)
            class_hIcon = win32gui.GetClassLong(hwnd, win32con.GCL_HICON)
            class_hCursor = win32gui.GetClassLong(hwnd, win32con.GCL_HCURSOR)
            class_hbrBackground = win32gui.GetClassLong(hwnd, win32con.GCL_HBRBACKGROUND)
            class_lpszMenuName = win32gui.GetClassLong(hwnd, win32con.GCL_MENUNAME)
            
            return f"""类名: {class_name}
类原子: {class_atom}
类样式: 0x{class_style:08X}
窗口额外字节: {class_cbWndExtra}
类额外字节: {class_cbClsExtra}
实例句柄: {class_hInstance} (0x{class_hInstance:08X})
图标句柄: {class_hIcon} (0x{class_hIcon:08X})
光标句柄: {class_hCursor} (0x{class_hCursor:08X})
背景画刷: {class_hbrBackground} (0x{class_hbrBackground:08X})
菜单名: {class_lpszMenuName}"""
        except Exception as e:
            return f"类名: {class_name}\n获取详细信息失败: {e}"
    
    def _get_class_style_info(self) -> str:
        hwnd = self._hwnd
        
        try:
            class_style = win32gui.GetClassLong(hwnd, win32con.GCL_STYLE)
            
            class_styles = {
                win32con.CS_VREDRAW: ("CS_VREDRAW", "窗口高度改变时重绘"),
                win32con.CS_HREDRAW: ("CS_HREDRAW", "窗口宽度改变时重绘"),
                win32con.CS_DBLCLKS: ("CS_DBLCLKS", "支持双击消息"),
                win32con.CS_OWNDC: ("CS_OWNDC", "私有设备上下文"),
                win32con.CS_CLASSDC: ("CS_CLASSDC", "类设备上下文"),
                win32con.CS_PARENTDC: ("CS_PARENTDC", "使用父窗口DC"),
                win32con.CS_NOCLOSE: ("CS_NOCLOSE", "禁用关闭按钮"),
                win32con.CS_SAVEBITS: ("CS_SAVEBITS", "保存被覆盖区域"),
                win32con.CS_BYTEALIGNCLIENT: ("CS_BYTEALIGNCLIENT", "字节对齐客户区"),
                win32con.CS_BYTEALIGNWINDOW: ("CS_BYTEALIGNWINDOW", "字节对齐窗口"),
                win32con.CS_GLOBALCLASS: ("CS_GLOBALCLASS", "全局窗口类"),
            }
            
            style_list = []
            for flag, (name, desc) in sorted(class_styles.items()):
                if class_style & flag:
                    style_list.append(f"  {name}: {desc}")
            
            styles_str = "\n".join(style_list) if style_list else "  无"
            
            return f"""类样式值: 0x{class_style:08X}

包含样式:
{styles_str}"""
        except Exception:
            return "获取失败"
    
    def _get_all_properties(self) -> dict:
        hwnd = self._hwnd
        
        props = {}
        
        props["窗口标识"] = {
            "句柄": f"{hwnd} (0x{hwnd:08X})",
            "标题": self._window_info.get('title', '未知'),
            "类名": self._window_info.get('class_name', '未知'),
        }
        
        props["窗口状态"] = {
            "可见": self._safe_call(lambda: bool(win32gui.IsWindowVisible(hwnd)), False),
            "启用": self._safe_call(lambda: bool(win32gui.IsWindowEnabled(hwnd)), False),
            "最大化": self._safe_call(lambda: bool(win32gui.IsZoomed(hwnd)), False),
            "最小化": self._safe_call(lambda: bool(win32gui.IsIconic(hwnd)), False),
            "前台": self._safe_call(lambda: win32gui.GetForegroundWindow() == hwnd, False),
        }
        
        props["窗口数据"] = {
            "窗口ID": self._safe_call(lambda: win32gui.GetWindowLong(hwnd, win32con.GWL_ID), 0),
            "用户数据": self._safe_call(lambda: win32gui.GetWindowLong(hwnd, win32con.GWL_USERDATA), 0),
            "实例句柄": f"0x{self._safe_call(lambda: win32gui.GetWindowLong(hwnd, win32con.GWL_HINSTANCE), 0):08X}",
        }
        
        props["进程线程"] = {
            "进程ID": self._window_info.get('process_id', 0),
            "线程ID": self._safe_call(lambda: win32process.GetWindowThreadProcessId(hwnd)[0], 0),
        }
        
        props["菜单信息"] = {
            "菜单句柄": f"0x{self._safe_call(lambda: win32gui.GetMenu(hwnd), 0):08X}",
            "系统菜单": f"0x{self._safe_call(lambda: win32gui.GetSystemMenu(hwnd, False), 0):08X}",
        }
        
        try:
            text_len = win32gui.SendMessage(hwnd, win32con.WM_GETTEXTLENGTH, 0, 0)
            props["文本信息"] = {
                "文本长度": text_len,
            }
        except Exception:
            pass
        
        return props


class WindowBinderPanel(QWidget):
    """
    窗口绑定面板
    
    包含：准星图标、窗口下拉框、绑定按钮、刷新按钮
    下方：窗口简要信息、解除绑定按钮、详情按钮
    """
    
    window_bound = Signal(dict)
    window_unbound = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._bound_window_info = None
        self._highlighter = None
        self._dragging_crosshair = None
        self._crosshair_dragging = False
        self._check_timer = QTimer()
        self._check_timer.timeout.connect(self._on_timer)
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)
        
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)
        
        self.crosshair = CrosshairIcon()
        self.crosshair.setToolTip("拖拽到目标窗口进行绑定")
        top_layout.addWidget(self.crosshair)
        
        self.window_combo = ArrowComboBox()
        self.window_combo.setToolTip("选择要绑定的窗口")
        top_layout.addWidget(self.window_combo, 1)
        
        self.bind_btn = QPushButton("绑定窗口")
        self.bind_btn.setFixedWidth(80)
        self.bind_btn.setToolTip("绑定下拉框中选中的窗口")
        self.bind_btn.clicked.connect(self._on_bind_selected)
        top_layout.addWidget(self.bind_btn)
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFixedWidth(60)
        self.refresh_btn.setToolTip("刷新窗口列表")
        self.refresh_btn.clicked.connect(self.refresh_window_list)
        top_layout.addWidget(self.refresh_btn)
        
        main_layout.addLayout(top_layout)
        
        self.info_frame = QFrame()
        info_layout = QHBoxLayout(self.info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)
        
        self.info_label = QLabel("未绑定窗口")
        self.info_label.setStyleSheet("color: #757575; font-size: 12px;")
        info_layout.addWidget(self.info_label, 1)
        
        self.unbind_btn = QPushButton("解除绑定")
        self.unbind_btn.setFixedWidth(80)
        self.unbind_btn.setVisible(False)
        self.unbind_btn.clicked.connect(self._on_unbind)
        info_layout.addWidget(self.unbind_btn)
        
        self.detail_btn = QPushButton("窗口详情")
        self.detail_btn.setFixedWidth(80)
        self.detail_btn.setVisible(False)
        self.detail_btn.clicked.connect(self._on_show_detail)
        info_layout.addWidget(self.detail_btn)
        
        self.toggle_visibility_btn = QPushButton("隐藏窗口")
        self.toggle_visibility_btn.setFixedWidth(80)
        self.toggle_visibility_btn.setVisible(False)
        self.toggle_visibility_btn.clicked.connect(self._on_toggle_visibility)
        info_layout.addWidget(self.toggle_visibility_btn)
        
        main_layout.addWidget(self.info_frame)
        
        self._apply_styles()
        self.refresh_window_list()
    
    def _apply_styles(self):
        self.setStyleSheet("""
            ArrowComboBox, QComboBox {
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                padding: 5px 30px 5px 10px;
                background: white;
                min-height: 28px;
            }
            ArrowComboBox:hover, QComboBox:hover {
                border-color: #1976D2;
            }
            QComboBox QAbstractItemView {
                border: 1px solid #BDBDBD;
                background: white;
                selection-background-color: #E3F2FD;
                selection-color: #1976D2;
            }
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #9E9E9E;
            }
        """)
    
    def refresh_window_list(self):
        """刷新窗口列表"""
        self.window_combo.clear()
        self._window_list = self._get_top_windows()
        
        for win_info in self._window_list:
            title = win_info['title']
            if len(title) > 40:
                title = title[:37] + "..."
            self.window_combo.addItem(title, win_info['hwnd'])
    
    def _get_top_windows(self) -> list:
        """获取所有可见窗口（包括子窗口）"""
        windows = []
        seen_hwnds = set()
        
        def add_window(hwnd):
            if hwnd in seen_hwnds:
                return
            if not win32gui.IsWindow(hwnd):
                return
            
            try:
                title = win32gui.GetWindowText(hwnd)
                class_name = win32gui.GetClassName(hwnd)
                _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                rect = win32gui.GetWindowRect(hwnd)
                
                windows.append({
                    'hwnd': hwnd,
                    'title': title if title else f"(无标题) - {class_name}",
                    'class_name': class_name,
                    'process_id': process_id,
                    'rect': rect,
                    'width': rect[2] - rect[0],
                    'height': rect[3] - rect[1]
                })
                seen_hwnds.add(hwnd)
            except Exception:
                pass
        
        def enum_child_windows(parent_hwnd):
            def child_callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    add_window(hwnd)
                    win32gui.EnumChildWindows(hwnd, child_callback, None)
                return True
            win32gui.EnumChildWindows(parent_hwnd, child_callback, None)
        
        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                add_window(hwnd)
                win32gui.EnumChildWindows(hwnd, lambda h, _: add_window(h) if win32gui.IsWindowVisible(h) else True, None)
            return True
        
        win32gui.EnumWindows(enum_callback, None)
        
        windows.sort(key=lambda w: (not w['title'].startswith("(无标题)"), w['title'].lower()))
        
        return windows
    
    def _on_bind_selected(self):
        """绑定下拉框中选中的窗口"""
        hwnd = self.window_combo.currentData()
        if hwnd:
            for win_info in self._window_list:
                if win_info['hwnd'] == hwnd:
                    self._bind_window(win_info)
                    self._flash_window(hwnd)
                    break
    
    def _flash_window(self, hwnd: int):
        """闪烁窗口边框"""
        if self._highlighter:
            self._highlighter.stop_highlight()
            self._highlighter.close()
        
        self._highlighter = WindowHighlighter()
        self._highlighter.start_highlight(hwnd, continuous=False)
    
    def _bind_window(self, window_info: dict):
        """绑定窗口"""
        self._bound_window_info = window_info
        title = window_info.get('title', '未知')
        width = window_info.get('width', 0)
        height = window_info.get('height', 0)
        
        self.info_label.setText(f"已绑定: {title[:30]} ({width}x{height})")
        self.info_label.setStyleSheet("color: #4CAF50; font-size: 12px; font-weight: bold;")
        self.unbind_btn.setVisible(True)
        self.detail_btn.setVisible(True)
        self.toggle_visibility_btn.setVisible(True)
        self.toggle_visibility_btn.setText("隐藏窗口")
        
        self.window_bound.emit(window_info)
    
    def _on_unbind(self):
        """解除绑定"""
        self._bound_window_info = None
        self.info_label.setText("未绑定窗口")
        self.info_label.setStyleSheet("color: #757575; font-size: 12px;")
        self.unbind_btn.setVisible(False)
        self.detail_btn.setVisible(False)
        self.toggle_visibility_btn.setVisible(False)
        self.window_unbound.emit()
    
    def _on_toggle_visibility(self):
        """切换窗口显示/隐藏"""
        if not self._bound_window_info:
            return
        
        hwnd = self._bound_window_info['hwnd']
        try:
            if win32gui.IsWindowVisible(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                self.toggle_visibility_btn.setText("显示窗口")
            else:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                self.toggle_visibility_btn.setText("隐藏窗口")
        except Exception as e:
            pass
    
    def _on_show_detail(self):
        """显示窗口详情"""
        if self._bound_window_info:
            dialog = WindowDetailDialog(self._bound_window_info, self)
            dialog.exec()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            crosshair_rect = self.crosshair.geometry()
            if crosshair_rect.contains(event.pos()):
                self._crosshair_dragging = True
                self.crosshair.set_dragging(True)
                
                self._dragging_crosshair = DraggingCrosshair()
                self._dragging_crosshair.move_to_cursor()
                self._dragging_crosshair.show()
                
                self._highlighter = WindowHighlighter()
                self._check_timer.start(30)
                self.grabMouse()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._crosshair_dragging:
            self._crosshair_dragging = False
            self.crosshair.set_dragging(False)
            self._check_timer.stop()
            self.releaseMouse()
            
            if self._dragging_crosshair:
                self._dragging_crosshair.close()
                self._dragging_crosshair = None
            
            if self._highlighter:
                self._highlighter.stop_highlight()
                self._highlighter.close()
                self._highlighter = None
            
            hwnd = self._get_window_at_cursor()
            if hwnd:
                win_info = None
                for info in self._window_list:
                    if info['hwnd'] == hwnd:
                        win_info = info
                        break
                
                if not win_info:
                    try:
                        title = win32gui.GetWindowText(hwnd)
                        class_name = win32gui.GetClassName(hwnd)
                        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
                        rect = win32gui.GetWindowRect(hwnd)
                        win_info = {
                            'hwnd': hwnd,
                            'title': title if title else f"(无标题) - {class_name}",
                            'class_name': class_name,
                            'process_id': process_id,
                            'rect': rect,
                            'width': rect[2] - rect[0],
                            'height': rect[3] - rect[1]
                        }
                    except Exception:
                        pass
                
                if win_info:
                    self._bind_window(win_info)
                    self.refresh_window_list()
                    idx = self.window_combo.findData(hwnd)
                    if idx >= 0:
                        self.window_combo.setCurrentIndex(idx)
            
            self.crosshair.set_hover(False)
            QApplication.setOverrideCursor(Qt.ArrowCursor)
    
    def _on_timer(self):
        """定时检查鼠标位置"""
        if not self._crosshair_dragging:
            return
        
        if self._dragging_crosshair:
            self._dragging_crosshair.move_to_cursor()
        
        hwnd = self._get_window_at_cursor()
        if hwnd and self._highlighter:
            self._highlighter.start_highlight(hwnd, continuous=True)
    
    def _get_window_at_cursor(self) -> int:
        """获取鼠标下的窗口句柄（包括子窗口）"""
        try:
            cursor_pos = win32api.GetCursorPos()
            hwnd = win32gui.WindowFromPoint(cursor_pos)
            
            if hwnd == 0:
                return None
            
            self_hwnd = int(self.winId())
            if hwnd == self_hwnd:
                return None
            
            return hwnd
        except Exception:
            return None
    
    def get_bound_window(self) -> dict:
        """获取绑定的窗口信息"""
        return self._bound_window_info
    
    def clear_binding(self):
        """清除绑定"""
        self._on_unbind()
