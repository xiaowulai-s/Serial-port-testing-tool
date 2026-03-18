from abc import ABC, abstractmethod
from typing import Optional, Union, Any
from PyQt5.QtCore import QObject, pyqtSignal


class ProtocolPlugin(ABC):
    """协议插件基类 - 所有自定义协议插件必须继承此类"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_enabled = True
    
    @abstractmethod
    def parse(self, data: bytes) -> Optional[Any]:
        """
        解析接收到的数据
        
        Args:
            data: 接收到的原始字节数据
            
        Returns:
            解析后的结果，如果无法解析返回 None
        """
        pass
    
    @abstractmethod
    def format_for_display(self, parsed_data: Any) -> str:
        """
        将解析后的数据格式化为显示文本
        
        Args:
            parsed_data: parse() 方法返回的解析结果
            
        Returns:
            格式化后的显示字符串
        """
        pass
    
    @abstractmethod
    def encode(self, data: Any) -> Optional[bytes]:
        """
        将数据编码为可发送的字节序列
        
        Args:
            data: 要编码的数据
            
        Returns:
            编码后的字节数据，如果无法编码返回 None
        """
        pass


class RawPlugin(ProtocolPlugin):
    """原始数据协议插件 - 默认插件"""
    
    def __init__(self):
        super().__init__("Raw")
    
    def parse(self, data: bytes) -> bytes:
        return data
    
    def format_for_display(self, parsed_data: bytes) -> str:
        return parsed_data.decode('utf-8', errors='replace')
    
    def encode(self, data: str) -> Optional[bytes]:
        if isinstance(data, str):
            return data.encode('utf-8')
        elif isinstance(data, bytes):
            return data
        return None


class HexPlugin(ProtocolPlugin):
    """十六进制协议插件"""
    
    def __init__(self):
        super().__init__("Hex")
    
    def parse(self, data: bytes) -> bytes:
        return data
    
    def format_for_display(self, parsed_data: bytes) -> str:
        return ' '.join(f'{b:02X}' for b in parsed_data) + ' '
    
    def encode(self, data: str) -> Optional[bytes]:
        if isinstance(data, str):
            try:
                hex_str = data.replace(' ', '')
                return bytes.fromhex(hex_str)
            except:
                return None
        elif isinstance(data, bytes):
            return data
        return None


class DataParser(QObject):
    """数据解析器 - 管理和使用协议插件"""
    
    parsed_data_ready = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.plugins: dict[str, ProtocolPlugin] = {}
        self.active_plugin: Optional[str] = None
        
        # 注册默认插件
        self.register_plugin(RawPlugin())
        self.register_plugin(HexPlugin())
        
        # 默认激活 Raw 插件
        self.set_active_plugin("Raw")
    
    def register_plugin(self, plugin: ProtocolPlugin):
        """
        注册新的协议插件
        
        Args:
            plugin: 继承自 ProtocolPlugin 的插件实例
        """
        self.plugins[plugin.name] = plugin
    
    def unregister_plugin(self, plugin_name: str):
        """
        注销协议插件
        
        Args:
            plugin_name: 要注销的插件名称
        """
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
            if self.active_plugin == plugin_name:
                self.active_plugin = None
    
    def get_plugin_names(self) -> list[str]:
        """
        获取所有已注册插件的名称
        
        Returns:
            插件名称列表
        """
        return list(self.plugins.keys())
    
    def set_active_plugin(self, plugin_name: str) -> bool:
        """
        设置当前使用的插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否设置成功
        """
        if plugin_name in self.plugins:
            self.active_plugin = plugin_name
            return True
        return False
    
    def parse_data(self, data: bytes) -> Optional[str]:
        """
        解析数据并格式化为显示文本
        
        Args:
            data: 原始字节数据
            
        Returns:
            格式化后的显示字符串
        """
        if self.active_plugin and self.active_plugin in self.plugins:
            plugin = self.plugins[self.active_plugin]
            parsed = plugin.parse(data)
            if parsed is not None:
                formatted = plugin.format_for_display(parsed)
                self.parsed_data_ready.emit(formatted)
                return formatted
        return None
    
    def encode_data(self, data: Union[str, Any]) -> Optional[bytes]:
        """
        编码数据为字节序列
        
        Args:
            data: 要编码的数据
            
        Returns:
            编码后的字节数据
        """
        if self.active_plugin and self.active_plugin in self.plugins:
            plugin = self.plugins[self.active_plugin]
            return plugin.encode(data)
        return None
