# 串口测试工具 - 架构说明

## 项目架构

本项目采用三层架构设计，实现了高度的模块化和解耦：

```
┌─────────────────────────────────────────────────┐
│                  UI层 (View)                     │
│  main_window.py, home_interface.py, setting     │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│              业务逻辑层 (Business Logic)         │
│  ┌─────────────────┐  ┌──────────────────────┐ │
│  │ SerialManager   │  │ DataParser           │ │
│  │ (串口管理器)    │  │ (数据解析器)         │ │
│  └─────────────────┘  └──────────────────────┘ │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│              插件层 (Plugins)                    │
│  ProtocolPlugin (协议插件基类)                   │
│  ├── RawPlugin (原始数据)                        │
│  ├── HexPlugin (十六进制)                        │
│  └── ModbusPlugin (示例协议)                     │
└─────────────────────────────────────────────────┘
```

## 核心模块说明

### 1. serial_manager.py - 串口管理器

**职责**：负责串口的生命周期管理和通信

**核心类**：

- **SerialWorker** (QThread)：
  - 独立线程，负责持续监听和读取串口数据
  - 通过信号 `data_received`、`error_occurred`、`connection_lost` 与主线程通信

- **SerialConfig**：
  - 串口配置类，封装所有串口参数
  - 包含波特率、数据位、停止位、校验位等配置

- **SerialManager** (QObject)：
  - 串口管理器，负责串口的打开/关闭
  - 提供静态方法 `get_available_ports()` 扫描可用串口
  - 发送数据通过 `send_data()` 方法

### 2. data_parser.py - 数据解析器

**职责**：管理和使用协议插件，处理数据的编码和解码

**核心类**：

- **ProtocolPlugin** (ABC)：
  - 协议插件基类，所有自定义协议必须继承此类
  - 定义了三个抽象方法：`parse()`、`format_for_display()`、`encode()`

- **RawPlugin**：
  - 原始数据插件，默认插件
  - 直接使用 UTF-8 编码/解码

- **HexPlugin**：
  - 十六进制插件
  - 以十六进制格式显示和发送数据

- **DataParser** (QObject)：
  - 插件管理器，负责注册、注销和切换插件
  - 通过 `parsed_data_ready` 信号发送解析后的数据

### 3. home_interface.py - 首页界面

**职责**：UI 展示和用户交互

**主要功能**：
- 左侧：串口设置面板
- 右侧：数据接收和发送区
- 协议选择下拉框
- 定时发送功能

## 如何添加自定义协议插件

### 步骤 1：创建插件类

在 `app/plugins/` 目录下创建新的插件文件，例如 `my_protocol.py`：

```python
from typing import Optional, Any
from app.data_parser import ProtocolPlugin

class MyProtocolPlugin(ProtocolPlugin):
    def __init__(self):
        super().__init__("MyProtocol")
    
    def parse(self, data: bytes) -> Optional[Any]:
        """解析接收到的数据"""
        # 实现你的解析逻辑
        pass
    
    def format_for_display(self, parsed_data: Any) -> str:
        """将解析后的数据格式化为显示文本"""
        # 实现你的格式化逻辑
        pass
    
    def encode(self, data: Any) -> Optional[bytes]:
        """编码数据为字节序列"""
        # 实现你的编码逻辑
        pass
```

### 步骤 2：注册插件

在 `home_interface.py` 中导入并注册插件：

```python
from app.plugins.my_protocol import MyProtocolPlugin

# 在 __init__ 方法中
self.data_parser.register_plugin(MyProtocolPlugin())
self.update_protocol_combo()
```

### 步骤 3：使用插件

启动程序后，在"协议"下拉框中选择你的协议即可使用。

## 信号和槽连接

```
SerialManager
  ├─ port_opened → HomeInterface.on_port_opened
  ├─ port_closed → HomeInterface.on_port_closed
  ├─ data_received → HomeInterface.on_data_received
  └─ error_occurred → HomeInterface.on_error

DataParser
  └─ parsed_data_ready → (可选，用于其他组件)

SerialWorker
  ├─ data_received → SerialManager._on_data_received
  ├─ error_occurred → SerialManager._on_error
  └─ connection_lost → SerialManager._on_connection_lost
```

## 设计原则

1. **单一职责原则**：每个类只负责一个功能
2. **开闭原则**：对扩展开放，对修改关闭（通过插件系统）
3. **依赖倒置原则**：UI 依赖抽象（SerialManager、DataParser），不依赖具体实现
4. **接口隔离原则**：ProtocolPlugin 定义了清晰的接口
