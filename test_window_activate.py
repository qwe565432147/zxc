"""
窗口激活测试脚本
================

用于测试窗口的最小化恢复和激活功能
"""

import time
import ctypes
import win32gui
import win32con
import win32api
import win32process


def get_window_info(hwnd):
    """获取窗口信息"""
    try:
        title = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        rect = win32gui.GetWindowRect(hwnd)
        _, process_id = win32process.GetWindowThreadProcessId(hwnd)
        
        is_visible = win32gui.IsWindowVisible(hwnd)
        is_iconic = win32gui.IsIconic(hwnd)
        is_enabled = win32gui.IsWindowEnabled(hwnd)
        
        return {
            'hwnd': hwnd,
            'title': title,
            'class_name': class_name,
            'rect': rect,
            'process_id': process_id,
            'is_visible': is_visible,
            'is_iconic': is_iconic,
            'is_enabled': is_enabled
        }
    except Exception as e:
        return {'error': str(e)}


def print_window_info(hwnd):
    """打印窗口信息"""
    info = get_window_info(hwnd)
    if 'error' in info:
        print(f"获取窗口信息失败: {info['error']}")
        return
    
    print(f"\n窗口信息:")
    print(f"  句柄: {info['hwnd']}")
    print(f"  标题: {info['title']}")
    print(f"  类名: {info['class_name']}")
    print(f"  位置: {info['rect']}")
    print(f"  进程ID: {info['process_id']}")
    print(f"  可见: {info['is_visible']}")
    print(f"  最小化: {info['is_iconic']}")
    print(f"  启用: {info['is_enabled']}")


def activate_window(hwnd):
    """激活窗口"""
    print(f"\n尝试激活窗口 {hwnd}...")
    
    try:
        if not win32gui.IsWindow(hwnd):
            print("错误: 无效的窗口句柄")
            return False
        
        print(f"窗口有效")
        
        is_iconic = win32gui.IsIconic(hwnd)
        is_visible = win32gui.IsWindowVisible(hwnd)
        print(f"最小化状态: {is_iconic}, 可见状态: {is_visible}")
        
        if is_iconic:
            print("窗口已最小化，正在恢复...")
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.3)
            print(f"恢复后 - 最小化: {win32gui.IsIconic(hwnd)}, 可见: {win32gui.IsWindowVisible(hwnd)}")
        
        if not win32gui.IsWindowVisible(hwnd):
            print("窗口不可见，正在显示...")
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            time.sleep(0.1)
        
        print("尝试方法1: AttachThreadInput...")
        try:
            foreground_hwnd = win32gui.GetForegroundWindow()
            foreground_thread = win32process.GetWindowThreadProcessId(foreground_hwnd)[0]
            current_thread = win32api.GetCurrentThreadId()
            target_thread = win32process.GetWindowThreadProcessId(hwnd)[0]
            
            print(f"前台窗口线程: {foreground_thread}, 当前线程: {current_thread}, 目标线程: {target_thread}")
            
            if current_thread != foreground_thread:
                ctypes.windll.user32.AttachThreadInput(current_thread, foreground_thread, True)
                print("已连接当前线程和前台线程")
            
            win32gui.BringWindowToTop(hwnd)
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            result = win32gui.SetForegroundWindow(hwnd)
            print(f"SetForegroundWindow 返回: {result}")
            win32gui.SetFocus(hwnd)
            
            if current_thread != foreground_thread:
                ctypes.windll.user32.AttachThreadInput(current_thread, foreground_thread, False)
                print("已断开线程连接")
        except Exception as e:
            print(f"方法1失败: {e}")
        
        current_fg = win32gui.GetForegroundWindow()
        print(f"当前前台窗口: {current_fg}, 目标窗口: {hwnd}")
        
        if current_fg != hwnd:
            print("方法1未成功，尝试方法2: Alt键技巧...")
            keybd_event = ctypes.windll.user32.keybd_event
            
            keybd_event(0x12, 0, 0, 0)
            keybd_event(0x12, 0, 2, 0)
            
            win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
            win32gui.SetForegroundWindow(hwnd)
            
            keybd_event(0x12, 0, 0, 0)
            keybd_event(0x12, 0, 2, 0)
            
            time.sleep(0.2)
        
        current_fg = win32gui.GetForegroundWindow()
        print(f"最终前台窗口: {current_fg}, 目标窗口: {hwnd}")
        
        if current_fg == hwnd:
            print("成功: 窗口已激活到前台!")
            return True
        else:
            print("失败: 窗口未能激活到前台")
            return False
            
    except Exception as e:
        print(f"激活失败: {e}")
        return False


def minimize_window(hwnd):
    """最小化窗口"""
    try:
        print(f"\n最小化窗口 {hwnd}...")
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
        time.sleep(0.2)
        print(f"最小化后状态 - 最小化: {win32gui.IsIconic(hwnd)}, 可见: {win32gui.IsWindowVisible(hwnd)}")
        return True
    except Exception as e:
        print(f"最小化失败: {e}")
        return False


def list_windows():
    """列出所有可见窗口"""
    windows = []
    
    def enum_callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:
                windows.append((hwnd, title))
        return True
    
    win32gui.EnumWindows(enum_callback, None)
    return windows


def main():
    print("=" * 50)
    print("窗口激活测试脚本")
    print("=" * 50)
    
    while True:
        print("\n选项:")
        print("1. 列出所有窗口")
        print("2. 输入窗口句柄测试")
        print("3. 鼠标选择窗口")
        print("4. 退出")
        
        choice = input("\n请选择 (1-4): ").strip()
        
        if choice == '1':
            print("\n可见窗口列表:")
            windows = list_windows()
            for hwnd, title in windows[:20]:
                print(f"  {hwnd}: {title[:50]}")
            if len(windows) > 20:
                print(f"  ... 还有 {len(windows) - 20} 个窗口")
        
        elif choice == '2':
            hwnd_str = input("请输入窗口句柄 (十进制或0x开头的十六进制): ").strip()
            try:
                if hwnd_str.startswith('0x'):
                    hwnd = int(hwnd_str, 16)
                else:
                    hwnd = int(hwnd_str)
                
                print_window_info(hwnd)
                
                print("\n操作:")
                print("1. 最小化窗口")
                print("2. 激活窗口")
                print("3. 返回")
                
                op = input("请选择操作 (1-3): ").strip()
                if op == '1':
                    minimize_window(hwnd)
                elif op == '2':
                    activate_window(hwnd)
                    
            except ValueError:
                print("无效的句柄格式")
        
        elif choice == '3':
            print("\n请将鼠标移动到目标窗口上...")
            time.sleep(2)
            
            cursor_pos = win32api.GetCursorPos()
            hwnd = win32gui.WindowFromPoint(cursor_pos)
            
            print(f"\n鼠标位置: {cursor_pos}")
            print(f"窗口句柄: {hwnd}")
            print_window_info(hwnd)
            
            print("\n操作:")
            print("1. 最小化窗口")
            print("2. 激活窗口")
            print("3. 返回")
            
            op = input("请选择操作 (1-3): ").strip()
            if op == '1':
                minimize_window(hwnd)
            elif op == '2':
                activate_window(hwnd)
        
        elif choice == '4':
            print("退出测试脚本")
            break
        
        else:
            print("无效选择")


if __name__ == '__main__':
    main()
