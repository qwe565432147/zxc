"""
倒计时管理模块
==============

这个模块负责管理倒计时功能，包括：
- 设置倒计时时间
- 启动/暂停/重置倒计时
- 倒计时结束触发回调

对于新手来说，理解这个模块需要知道：
1. QTimer是PySide6提供的定时器类，可以定时触发信号
2. 信号和槽是Qt框架的核心机制，用于对象间通信
3. 回调函数是一种在特定事件发生时自动调用的函数
"""

from PySide6.QtCore import QObject, QTimer, Signal
from datetime import datetime, timedelta
from typing import Callable, Optional


class CountdownManager(QObject):
    """
    倒计时管理器类
    
    这个类负责管理整个倒计时过程，包括时间的计算、更新和触发。
    
    继承自QObject的原因：
    - QObject是Qt所有对象的基类
    - 需要使用Qt的信号槽机制
    - 需要使用QTimer定时器
    
    属性说明：
    - remaining_seconds: 剩余秒数
    - is_running: 是否正在运行
    - is_paused: 是否已暂停
    """
    
    # ========== 信号定义 ==========
    # 信号是Qt中用于对象间通信的机制
    # 当信号被emit（发射）时，连接到该信号的槽函数会被调用
    
    # 倒计时更新信号，每秒发射一次，携带剩余秒数
    time_updated = Signal(int)
    
    # 倒计时结束信号
    countdown_finished = Signal()
    
    # 状态变化信号，携带状态字符串
    status_changed = Signal(str)
    
    def __init__(self, parent: Optional[QObject] = None):
        """
        初始化倒计时管理器
        
        参数：
            parent: 父对象，用于Qt对象树管理
                   如果指定了父对象，当父对象被销毁时，此对象也会被销毁
        """
        super().__init__(parent)
        
        # ========== 初始化属性 ==========
        self._remaining_seconds: int = 0      # 剩余秒数
        self._initial_seconds: int = 0        # 初始设置的秒数（用于重置）
        self._is_running: bool = False        # 是否正在运行
        self._is_paused: bool = False         # 是否已暂停
        self._end_time: Optional[datetime] = None  # 结束时间点
        
        # ========== 创建定时器 ==========
        # QTimer是Qt提供的定时器类
        # 它会按照设定的时间间隔，定时发射timeout信号
        self._timer = QTimer(self)
        
        # 设置定时器间隔为1000毫秒（1秒）
        self._timer.setInterval(1000)
        
        # 连接定时器的timeout信号到我们的更新方法
        # 当定时器超时时，会自动调用_on_timer_timeout方法
        self._timer.timeout.connect(self._on_timer_timeout)
        
        # 结束时的回调函数
        self._finish_callback: Optional[Callable] = None
    
    # ========== 属性访问器 ==========
    # 使用@property装饰器可以将方法变成属性访问
    # 这样可以像访问普通属性一样调用方法，如: manager.remaining_seconds
    
    @property
    def remaining_seconds(self) -> int:
        """获取剩余秒数"""
        return self._remaining_seconds
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self._is_running
    
    @property
    def is_paused(self) -> bool:
        """是否已暂停"""
        return self._is_paused
    
    # ========== 公共方法 ==========
    
    def set_countdown(self, hours: int, minutes: int, seconds: int) -> None:
        """
        设置倒计时时间
        
        这个方法会计算总的秒数并存储，但不会自动开始倒计时。
        
        参数：
            hours: 小时数
            minutes: 分钟数
            seconds: 秒数
            
        示例：
            manager.set_countdown(1, 30, 0)  # 设置1小时30分钟
        """
        # 计算总秒数：小时*3600 + 分钟*60 + 秒
        total_seconds = hours * 3600 + minutes * 60 + seconds
        
        self._remaining_seconds = total_seconds
        self._initial_seconds = total_seconds  # 保存初始值用于重置
        
        # 发射更新信号，通知UI更新显示
        self.time_updated.emit(total_seconds)
        
        # 更新状态
        self.status_changed.emit("已就绪")
    
    def set_countdown_from_seconds(self, total_seconds: int) -> None:
        """
        直接用秒数设置倒计时
        
        参数：
            total_seconds: 总秒数
        """
        self._remaining_seconds = total_seconds
        self._initial_seconds = total_seconds
        self.time_updated.emit(total_seconds)
        self.status_changed.emit("已就绪")
    
    def start(self) -> bool:
        """
        开始倒计时
        
        返回：
            bool: 是否成功开始
                  如果时间已设置为0或已经在运行，则返回False
        """
        # 检查是否可以开始
        if self._remaining_seconds <= 0:
            self.status_changed.emit("错误：请先设置倒计时时间")
            return False
        
        if self._is_running and not self._is_paused:
            # 已经在运行且未暂停
            return False
        
        # 如果是从暂停状态恢复
        if self._is_paused:
            self._is_paused = False
            self._is_running = True
            self._timer.start()
            self.status_changed.emit("运行中")
            return True
        
        # 全新开始
        self._is_running = True
        self._is_paused = False
        
        # 计算结束时间点
        # 这种方式比每次减1秒更精确，因为定时器可能有小误差
        self._end_time = datetime.now() + timedelta(seconds=self._remaining_seconds)
        
        # 启动定时器
        self._timer.start()
        
        self.status_changed.emit("运行中")
        return True
    
    def pause(self) -> None:
        """
        暂停倒计时
        
        暂停后可以调用start()恢复
        """
        if self._is_running and not self._is_paused:
            self._timer.stop()
            self._is_paused = True
            self.status_changed.emit("已暂停")
    
    def reset(self) -> None:
        """
        重置倒计时
        
        将倒计时恢复到最初设置的时间
        """
        # 停止定时器
        self._timer.stop()
        
        # 重置状态
        self._is_running = False
        self._is_paused = False
        self._remaining_seconds = self._initial_seconds
        self._end_time = None
        
        # 发射信号
        self.time_updated.emit(self._remaining_seconds)
        self.status_changed.emit("已重置")
    
    def stop(self) -> None:
        """
        完全停止倒计时
        
        与reset不同，这会将时间清零
        """
        self._timer.stop()
        self._is_running = False
        self._is_paused = False
        self._remaining_seconds = 0
        self._end_time = None
        
        self.time_updated.emit(0)
        self.status_changed.emit("已停止")
    
    def set_finish_callback(self, callback: Callable) -> None:
        """
        设置倒计时结束时的回调函数
        
        参数：
            callback: 无参数的回调函数
            
        示例：
            def on_finish():
                print("倒计时结束！")
            manager.set_finish_callback(on_finish)
        """
        self._finish_callback = callback
    
    # ========== 私有方法 ==========
    
    def _on_timer_timeout(self) -> None:
        """
        定时器超时处理方法
        
        这个方法每秒被调用一次，用于更新剩余时间。
        这是Qt信号槽机制的典型用法：
        1. 定时器发射timeout信号
        2. 这个方法作为槽函数被调用
        """
        if self._end_time:
            # 使用结束时间计算剩余时间，更精确
            now = datetime.now()
            if now >= self._end_time:
                # 时间到！
                self._remaining_seconds = 0
            else:
                # 计算剩余秒数
                delta = self._end_time - now
                self._remaining_seconds = int(delta.total_seconds())
        else:
            # 备用方案：直接减1秒
            self._remaining_seconds -= 1
        
        # 发射更新信号
        self.time_updated.emit(self._remaining_seconds)
        
        # 检查是否结束
        if self._remaining_seconds <= 0:
            self._on_countdown_finished()
    
    def _on_countdown_finished(self) -> None:
        """
        倒计时结束处理
        
        当倒计时归零时调用此方法
        """
        # 停止定时器
        self._timer.stop()
        self._is_running = False
        self._is_paused = False
        
        # 发射结束信号
        self.countdown_finished.emit()
        self.status_changed.emit("已完成")
        
        # 调用回调函数（如果设置了的话）
        if self._finish_callback:
            try:
                self._finish_callback()
            except Exception as e:
                # 如果回调函数出错，打印错误但不中断程序
                print(f"回调函数执行出错: {e}")
    
    @staticmethod
    def format_time(seconds: int) -> str:
        """
        将秒数格式化为 HH:MM:SS 格式的字符串
        
        这是一个静态方法，可以直接通过类名调用，不需要实例
        
        参数：
            seconds: 总秒数
            
        返回：
            格式化的时间字符串，如 "01:30:45"
            
        示例：
            CountdownManager.format_time(5445)  # 返回 "01:30:45"
        """
        # 计算小时、分钟、秒
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        # 使用f-string格式化，:02d表示两位数字，不足补0
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
