# 串口测试工具

一个基于 PyQt5 和 pyserial 的专业串口调试助手，具有完整的 Windows 11 风格交互体验。

## 功能特性

### 核心功能
- 自动检测电脑可用 COM 口
- 支持标准串口参数配置（波特率、数据位、停止位、校验位）
- 支持打开/关闭串口，实时状态更新
- 使用 QThread 多线程读取串口数据，避免界面卡顿
- 支持 Hex（十六进制）和 ASCII 两种显示/发送模式切换

### 高级功能
- 串口状态指示灯（绿色=已连接，红色=未连接）
- 自动保存 CSV 功能，实时导出接收数据
- 快捷指令侧边栏，支持保存常用的 AT 指令或调试命令
- 定时循环发送功能
- 清空接收区、一键保存接收到的日志到文件

### 扩展架构
- 三层架构设计（UI 层、业务逻辑层、插件层）
- 插件系统支持自定义数据解析协议
- 内置 Modbus 协议示例插件

## 技术栈

- Python 3.x
- PyQt5 - UI 框架
- pyserial - 串口通信
- pyqtSignal - 信号槽机制实现线程间通信

## 项目结构

```
Serial-port-testing-tool/
├── app/
│   ├── __init__.py
│   ├── home_interface.py      # 首页 - 串口通信主界面
│   ├── main_window.py          # 主窗口 - 侧边栏导航
│   ├── setting_interface.py    # 设置页面
│   ├── serial_manager.py       # 串口管理器（业务逻辑层）
│   ├── data_parser.py          # 数据解析器（插件系统）
│   └── plugins/
│       ├── __init__.py
│       └── modbus_plugin.py    # Modbus 协议示例插件
├── main.py                      # 程序入口
├── requirements.txt             # 依赖库列表
├── ARCHITECTURE.md              # 架构说明文档
└── README.md                    # 本文件
```

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python main.py
```

## 使用说明

### 基本使用
1. 程序启动后会自动扫描可用串口
2. 在左侧设置面板配置串口参数（串口号、波特率、数据位、停止位、校验位）
3. 点击"打开串口"按钮连接串口
4. 在右侧接收区查看接收到的数据
5. 在发送区输入数据并点击"发送"按钮发送数据

### 快捷指令
1. 点击"快捷指令"按钮打开指令面板
2. 点击"添加指令"可以保存常用的调试命令
3. 双击列表中的指令可以快速发送

### 自动保存
1. 点击"选择保存路径"设置 CSV 保存位置
2. 勾选"自动保存 CSV"开启自动保存功能
3. 程序每 5 秒自动保存一次接收数据

## 开发说明

### 添加自定义协议插件

在 `app/plugins/` 目录下创建新的插件文件，继承 `ProtocolPlugin` 抽象基类：

```python
from app.data_parser import ProtocolPlugin

class MyCustomPlugin(ProtocolPlugin):
    def get_name(self):
        return "MyProtocol"
    
    def parse_data(self, data: bytes) -> str:
        # 自定义数据解析逻辑
        pass
    
    def encode_data(self, text: str) -> bytes:
        # 自定义数据编码逻辑
        pass
```

在 `home_interface.py` 中注册插件：

```python
from app.plugins.my_custom_plugin import MyCustomPlugin

self.data_parser.register_plugin(MyCustomPlugin())
```

## 许可证

本项目仅供学习和个人使用。
