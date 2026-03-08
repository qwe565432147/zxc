# Auto Script Launcher

自动化脚本启动器 - 定时执行远程电脑上的自动化测试脚本

## 功能特点

- ⏰ **定时执行** - 设置倒计时，定时触发自动化任务
- 🖥️ **RDP 窗口绑定** - 通过拖拽绑定远程桌面窗口
- 🔄 **智能状态检测** - 自动检测 RDP 连接状态（已连接/断开/休眠）
- 🚀 **自动唤醒和重连** - 自动处理远程电脑休眠和断连
- 📊 **实时进度显示** - 百分比进度条显示执行状态

## 环境要求

- Python 3.12+
- Windows 操作系统
- pyenv-win + poetry (推荐)

## 安装

```bash
# 克隆仓库
git clone https://github.com/qwe565432147/zxc.git
cd zxc

# 安装依赖
poetry install
```

## 使用方法

```bash
# 启动程序
poetry run start

# 或者
poetry run python run.py
```

## 项目结构

```
zxc/
├── auto_launcher/
│   ├── core/           # 核心逻辑
│   │   ├── automation.py    # 自动化执行器
│   │   └── countdown.py     # 倒计时管理
│   ├── ui/             # 用户界面
│   │   ├── main_window.py   # 主窗口
│   │   └── window_binder.py # 窗口绑定控件
│   ├── utils/          # 工具模块
│   │   ├── image_recognition.py  # 图像识别
│   │   ├── screenshot_tool.py    # 截图工具
│   │   └── system_utils.py       # 系统工具
│   └── resources/      # 资源文件
│       └── templates/  # 图像模板
├── pyproject.toml      # 项目配置
└── run.py              # 启动入口
```

## 打包为 EXE

```bash
poetry run python build_exe.py
```

## License

MIT