"""
Modbus协议插件示例
展示如何创建自定义协议插件
"""
from typing import Optional, Any
from app.data_parser import ProtocolPlugin


class ModbusPlugin(ProtocolPlugin):
    """Modbus协议解析插件 - 示例实现"""
    
    def __init__(self):
        super().__init__("Modbus")
    
    def parse(self, data: bytes) -> Optional[dict]:
        """
        解析Modbus数据帧
        
        简单示例：检查是否符合Modbus基本格式
        """
        if len(data) >= 4:
            return {
                'address': data[0],
                'function': data[1],
                'data': data[2:-2],
                'crc': data[-2:]
            }
        return None
    
    def format_for_display(self, parsed_data: dict) -> str:
        """
        将Modbus数据格式化为显示文本
        """
        if parsed_data:
            return (f"地址: 0x{parsed_data['address']:02X}, "
                   f"功能码: 0x{parsed_data['function']:02X}, "
                   f"数据: {parsed_data['data'].hex()}\n")
        return ""
    
    def encode(self, data: Any) -> Optional[bytes]:
        """
        编码Modbus数据
        
        简单示例：直接返回字节数据
        """
        if isinstance(data, str):
            try:
                return bytes.fromhex(data.replace(' ', ''))
            except:
                return None
        elif isinstance(data, bytes):
            return data
        return None
