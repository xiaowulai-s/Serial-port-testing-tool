import serial
import serial.tools.list_ports
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from typing import Optional, Callable


class SerialWorker(QThread):
    """串口工作线程 - 负责监听和读取串口数据"""
    
    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    connection_lost = pyqtSignal()
    
    def __init__(self, serial_port: serial.Serial):
        super().__init__()
        self.serial_port = serial_port
        self.is_running = True
    
    def run(self):
        """持续读取串口数据"""
        while self.is_running and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    data = self.serial_port.read(self.serial_port.in_waiting)
                    self.data_received.emit(data)
            except Exception as e:
                self.error_occurred.emit(f"读取错误: {str(e)}")
                break
            self.msleep(10)
        
        if not self.serial_port.is_open:
            self.connection_lost.emit()
    
    def stop(self):
        """停止工作线程"""
        self.is_running = False
        self.wait()


class SerialConfig:
    """串口配置类"""
    
    PARITY_MAP = {
        '无': serial.PARITY_NONE,
        '奇': serial.PARITY_ODD,
        '偶': serial.PARITY_EVEN,
        'Mark': serial.PARITY_MARK,
        'Space': serial.PARITY_SPACE
    }
    
    STOPBITS_MAP = {
        '1': serial.STOPBITS_ONE,
        '1.5': serial.STOPBITS_ONE_POINT_FIVE,
        '2': serial.STOPBITS_TWO
    }
    
    def __init__(
        self,
        port: str = '',
        baudrate: int = 115200,
        bytesize: int = 8,
        stopbits: str = '1',
        parity: str = '无',
        timeout: float = 0.1
    ):
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.stopbits = stopbits
        self.parity = parity
        self.timeout = timeout


class SerialManager(QObject):
    """串口管理器 - 负责串口的生命周期管理"""
    
    # 信号定义
    port_opened = pyqtSignal(str)
    port_closed = pyqtSignal()
    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.serial_port: Optional[serial.Serial] = None
        self.worker: Optional[SerialWorker] = None
        self.config = SerialConfig()
    
    @staticmethod
    def get_available_ports() -> list[str]:
        """获取可用串口列表"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def open_port(self, config: SerialConfig) -> bool:
        """打开串口"""
        try:
            self.config = config
            
            # 关闭已有串口
            if self.is_open:
                self.close_port()
            
            # 创建并打开串口
            self.serial_port = serial.Serial(
                port=config.port,
                baudrate=config.baudrate,
                bytesize=config.bytesize,
                stopbits=SerialConfig.STOPBITS_MAP[config.stopbits],
                parity=SerialConfig.PARITY_MAP[config.parity],
                timeout=config.timeout
            )
            
            # 启动工作线程
            self.worker = SerialWorker(self.serial_port)
            self.worker.data_received.connect(self._on_data_received)
            self.worker.error_occurred.connect(self._on_error)
            self.worker.connection_lost.connect(self._on_connection_lost)
            self.worker.start()
            
            self.port_opened.emit(config.port)
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"打开串口失败: {str(e)}")
            return False
    
    def close_port(self):
        """关闭串口"""
        if self.worker:
            self.worker.stop()
            self.worker = None
        
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        
        self.serial_port = None
        self.port_closed.emit()
    
    def send_data(self, data: bytes) -> bool:
        """发送数据"""
        if not self.is_open:
            self.error_occurred.emit("串口未打开")
            return False
        
        try:
            self.serial_port.write(data)
            return True
        except Exception as e:
            self.error_occurred.emit(f"发送失败: {str(e)}")
            return False
    
    @property
    def is_open(self) -> bool:
        """检查串口是否打开"""
        return self.serial_port is not None and self.serial_port.is_open
    
    def _on_data_received(self, data: bytes):
        """接收到数据的回调"""
        self.data_received.emit(data)
    
    def _on_error(self, error_msg: str):
        """错误发生的回调"""
        self.error_occurred.emit(error_msg)
    
    def _on_connection_lost(self):
        """连接丢失的回调"""
        self.close_port()
        self.error_occurred.emit("串口连接已断开")
