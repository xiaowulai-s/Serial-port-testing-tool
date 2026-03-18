"""
DMT143 露点变送器协议插件
用于解析 Vaisala DMT143 设备的通信数据
"""
from typing import Optional, Any, Dict
import re
from app.data_parser import ProtocolPlugin


class DMT143Plugin(ProtocolPlugin):
    """DMT143 协议解析插件"""
    
    def __init__(self):
        super().__init__("DMT143")
        
        # 正则表达式用于解析测量数据
        # 匹配格式: Tdf= 17.75 'C Tdfatm= -5.25 'C H2O= 954 ppm
        self.measurement_pattern = re.compile(
            r'Tdf=\s*([-+]?\d+\.?\d*)\s*\'([CF])\s*'
            r'Tdfatm=\s*([-+]?\d+\.?\d*)\s*\'([CF])\s*'
            r'H2O=\s*(\d+\.?\d*)\s*ppm'
        )
        
        # 设备信息模式匹配
        self.device_info_pattern = re.compile(
            r'DMT143\s+([\d.]+)\s*'
            r'Serial number\s*:\s*(\S+)\s*'
            r'Batch number\s*:\s*(\S+)\s*'
            r'Sensor number\s*:\s*(\S+)\s*'
            r'Sensor model\s*:\s*(\S+)\s*'
            r'Cal\. date\s*:\s*(\S+)\s*'
            r'Cal\. info\s*:\s*(\S+)'
        )
    
    def parse(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        解析 DMT143 数据
        
        Args:
            data: 接收到的原始字节数据
            
        Returns:
            解析后的结果字典，如果无法解析返回 None
        """
        try:
            text = data.decode('ascii', errors='replace').strip()
            
            result = {
                'raw_data': text,
                'parse_steps': []
            }
            
            result['parse_steps'].append(f'步骤1: 接收到原始字节数据: {data.hex()}')
            result['parse_steps'].append(f'步骤2: 解码为ASCII文本: "{text}"')
            
            # 检查是否是设备信息响应
            if 'DMT143' in text and 'Serial number' in text:
                result['parse_steps'].append('步骤3: 识别为设备信息响应')
                device_info = self._parse_device_info(text)
                if device_info:
                    result.update(device_info)
                    result['parse_steps'].append('步骤4: 设备信息解析成功')
                return result
            
            # 检查是否是测量数据
            if 'Tdf=' in text and 'H2O=' in text:
                result['parse_steps'].append('步骤3: 识别为测量数据响应')
                measurement = self._parse_measurement(text)
                if measurement:
                    result.update(measurement)
                    result['parse_steps'].append('步骤4: 测量数据解析成功')
                    
                    # 添加温度单位转换
                    if 'tdf' in result and result['tdf_unit'] == 'F':
                        tdf_c = (result['tdf'] - 32) * 5/9
                        result['tdf_celsius'] = tdf_c
                        result['parse_steps'].append(f'步骤5: 华氏度转摄氏度: {result["tdf"]}°F → {tdf_c:.2f}°C')
                    
                    if 'tdfatm' in result and result['tdfatm_unit'] == 'F':
                        tdfatm_c = (result['tdfatm'] - 32) * 5/9
                        result['tdfatm_celsius'] = tdfatm_c
                        result['parse_steps'].append(f'步骤6: 大气压露点华氏度转摄氏度: {result["tdfatm"]}°F → {tdfatm_c:.2f}°C')
                
                return result
            
            # 检查是否是命令响应
            if ':' in text and not 'Tdf=' in text:
                result['parse_steps'].append('步骤3: 识别为命令响应')
                cmd_resp = self._parse_command_response(text)
                if cmd_resp:
                    result.update(cmd_resp)
                    result['parse_steps'].append('步骤4: 命令响应解析成功')
                return result
            
            result['parse_steps'].append('步骤3: 无法识别数据类型')
            return None
            
        except Exception as e:
            return None
    
    def _parse_device_info(self, text: str) -> Optional[Dict[str, Any]]:
        """解析设备信息"""
        match = self.device_info_pattern.search(text)
        if match:
            return {
                'type': 'device_info',
                'model': 'DMT143',
                'version': match.group(1),
                'serial_number': match.group(2),
                'batch_number': match.group(3),
                'sensor_number': match.group(4),
                'sensor_model': match.group(5),
                'cal_date': match.group(6),
                'cal_info': match.group(7)
            }
        return {'type': 'device_info', 'raw': text}
    
    def _parse_measurement(self, text: str) -> Optional[Dict[str, Any]]:
        """解析测量数据"""
        match = self.measurement_pattern.search(text)
        if match:
            return {
                'type': 'measurement',
                'tdf': float(match.group(1)),
                'tdf_unit': match.group(2),
                'tdfatm': float(match.group(3)),
                'tdfatm_unit': match.group(4),
                'h2o': float(match.group(5))
            }
        return {'type': 'measurement', 'raw': text}
    
    def _parse_command_response(self, text: str) -> Optional[Dict[str, Any]]:
        """解析命令响应"""
        lines = text.split('\n')
        result = {'type': 'command_response', 'responses': []}
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                result['responses'].append({
                    'key': key.strip(),
                    'value': value.strip()
                })
        
        if result['responses']:
            return result
        return {'type': 'command_response', 'raw': text}
    
    def format_for_display(self, parsed_data: Dict[str, Any]) -> str:
        """
        将解析后的数据格式化为显示文本
        
        Args:
            parsed_data: parse() 方法返回的解析结果
            
        Returns:
            格式化后的显示字符串
        """
        if not parsed_data:
            return ""
        
        display_text = ""
        
        if 'parse_steps' in parsed_data:
            display_text += "📝 解析过程:\n"
            for step in parsed_data['parse_steps']:
                display_text += f"   {step}\n"
            display_text += "\n"
        
        data_type = parsed_data.get('type', '')
        
        if data_type == 'measurement':
            if 'tdf' in parsed_data:
                display_text += (
                    f"📊 测量数据:\n"
                    f"   露点温度: {parsed_data['tdf']:.2f} °{parsed_data['tdf_unit']}\n"
                )
                if 'tdf_celsius' in parsed_data:
                    display_text += f"   露点(转换): {parsed_data['tdf_celsius']:.2f} °C\n"
                
                display_text += f"   大气压露点: {parsed_data['tdfatm']:.2f} °{parsed_data['tdfatm_unit']}\n"
                if 'tdfatm_celsius' in parsed_data:
                    display_text += f"   大气压露点(转换): {parsed_data['tdfatm_celsius']:.2f} °C\n"
                
                display_text += f"   湿度: {parsed_data['h2o']:.0f} ppm\n"
                display_text += f"{'='*50}\n"
            else:
                display_text += f"📊 测量数据: {parsed_data.get('raw', '')}\n"
        
        elif data_type == 'device_info':
            if 'version' in parsed_data:
                display_text += (
                    f"🔧 设备信息:\n"
                    f"   型号: {parsed_data['model']}\n"
                    f"   版本: {parsed_data['version']}\n"
                    f"   序列号: {parsed_data['serial_number']}\n"
                    f"   批次号: {parsed_data['batch_number']}\n"
                    f"   传感器型号: {parsed_data['sensor_model']}\n"
                    f"   校准日期: {parsed_data['cal_date']}\n"
                    f"{'='*50}\n"
                )
            else:
                display_text += f"🔧 设备信息:\n{parsed_data.get('raw', '')}\n{'='*50}\n"
        
        elif data_type == 'command_response':
            if 'responses' in parsed_data:
                display_text += "📋 命令响应:\n"
                for resp in parsed_data['responses']:
                    display_text += f"   {resp['key']}: {resp['value']}\n"
                display_text += f"{'='*50}\n"
            else:
                display_text += f"📋 命令响应:\n{parsed_data.get('raw', '')}\n{'='*50}\n"
        
        return display_text
    
    def encode(self, data: Any) -> Optional[bytes]:
        """
        将数据编码为可发送的字节序列
        
        Args:
            data: 要编码的数据（命令字符串）
            
        Returns:
            编码后的字节数据，如果无法编码返回 None
        """
        if isinstance(data, str):
            # DMT143 命令需要以回车符 <cr> 结束
            command = data.strip()
            if not command.endswith('\r'):
                command += '\r'
            return command.encode('ascii')
        elif isinstance(data, bytes):
            return data
        return None
