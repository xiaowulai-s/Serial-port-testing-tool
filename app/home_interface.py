import sys
import csv
from datetime import datetime
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, 
                             QTextEdit, QListWidget, QListWidgetItem,
                             QDialog, QFormLayout, QPushButton, QLabel,
                             QComboBox, QCheckBox, QSpinBox, QGroupBox, QLineEdit)
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont
from app.serial_manager import SerialManager, SerialConfig
from app.data_parser import DataParser
from app.plugins.modbus_plugin import ModbusPlugin
from app.plugins.dmt143_plugin import DMT143Plugin


class StatusDot(QWidget):
    """状态指示灯组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.is_on = False
        
    def set_status(self, is_on: bool):
        """设置状态"""
        self.is_on = is_on
        self.update()
        
    def paintEvent(self, event):
        """绘制指示灯"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        color = QColor(0, 200, 0) if self.is_on else QColor(200, 0, 0)
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(2, 2, 12, 12)


class QuickCommandDialog(QDialog):
    """添加快捷指令对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('添加快捷指令')
        self.resize(400, 200)
        
        layout = QFormLayout(self)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('指令名称（例如：AT测试）')
        layout.addRow('名称:', self.name_edit)
        
        self.command_edit = QLineEdit()
        self.command_edit.setPlaceholderText('指令内容（例如：AT+TEST）')
        layout.addRow('内容:', self.command_edit)
        
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton('确定')
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton('取消')
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addRow(btn_layout)
        
    def get_command(self):
        """获取输入的指令"""
        return self.name_edit.text(), self.command_edit.text()


class QuickCommandListDialog(QDialog):
    """快捷指令列表面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('快捷指令')
        self.resize(500, 400)
        self.selected_command = None
        
        layout = QVBoxLayout(self)
        
        title_label = QLabel('快捷指令')
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(14)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        self.command_list = QListWidget()
        self.command_list.itemDoubleClicked.connect(self.on_command_double_clicked)
        layout.addWidget(self.command_list)
        
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton('添加指令')
        self.add_btn.clicked.connect(self.add_quick_command)
        btn_layout.addWidget(self.add_btn)
        
        self.delete_btn = QPushButton('删除选中')
        self.delete_btn.clicked.connect(self.delete_quick_command)
        btn_layout.addWidget(self.delete_btn)
        
        self.close_btn = QPushButton('关闭')
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        
        self.quick_commands = []
    
    def set_commands(self, commands):
        """设置指令列表"""
        self.quick_commands = commands.copy()
        self.command_list.clear()
        for name, cmd in self.quick_commands:
            self.command_list.addItem(f'{name}: {cmd}')
    
    def get_commands(self):
        """获取指令列表"""
        return self.quick_commands
    
    def add_quick_command(self):
        """添加快捷指令"""
        dialog = QuickCommandDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, command = dialog.get_command()
            if name and command:
                self.quick_commands.append((name, command))
                self.command_list.addItem(f'{name}: {command}')
    
    def delete_quick_command(self):
        """删除快捷指令"""
        current_row = self.command_list.currentRow()
        if current_row >= 0:
            self.command_list.takeItem(current_row)
            del self.quick_commands[current_row]
    
    def on_command_double_clicked(self, item):
        """双击快捷指令"""
        index = self.command_list.row(item)
        if 0 <= index < len(self.quick_commands):
            _, command = self.quick_commands[index]
            self.selected_command = command
            self.accept()


class HomeInterface(QWidget):
    """首页 - 串口通信主界面"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('HomeInterface')
        
        self.serial_manager = SerialManager(self)
        self.data_parser = DataParser(self)
        self.data_parser.register_plugin(ModbusPlugin())
        self.data_parser.register_plugin(DMT143Plugin())
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_periodic_data)
        
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save_csv)
        self.auto_save_enabled = False
        self.auto_save_path = ''
        
        self.quick_commands = []
        
        self.latest_parsed_data = None
        
        self.init_ui()
        self.connect_signals()
        self.refresh_ports()
        self.update_protocol_combo()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_layout = QHBoxLayout()
        title_label = QLabel('串口测试工具')
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(18)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title_label, stretch=1)
        
        status_layout = QHBoxLayout()
        status_label = QLabel('串口状态:')
        self.status_dot = StatusDot()
        self.status_text = QLabel('未连接')
        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_dot)
        status_layout.addWidget(self.status_text)
        title_layout.addLayout(status_layout)
        
        layout.addLayout(title_layout)
        
        main_content_layout = QHBoxLayout()
        main_content_layout.setSpacing(20)
        
        self.create_settings_panel(main_content_layout)
        self.create_transceiver_panel(main_content_layout)
        
        layout.addLayout(main_content_layout)

    def create_settings_panel(self, parent_layout):
        """创建设置面板"""
        settings_group = QGroupBox('串口设置')
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(10)
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel('串口号:'))
        self.port_combo = QComboBox()
        port_layout.addWidget(self.port_combo)
        self.refresh_btn = QPushButton('刷新')
        self.refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.refresh_btn)
        settings_layout.addLayout(port_layout)

        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel('波特率:'))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(['9600', '19200', '38400', '57600', '115200'])
        self.baud_combo.setCurrentText('115200')
        baud_layout.addWidget(self.baud_combo)
        settings_layout.addLayout(baud_layout)

        data_layout = QHBoxLayout()
        data_layout.addWidget(QLabel('数据位:'))
        self.data_combo = QComboBox()
        self.data_combo.addItems(['5', '6', '7', '8'])
        self.data_combo.setCurrentText('8')
        data_layout.addWidget(self.data_combo)
        settings_layout.addLayout(data_layout)

        stop_layout = QHBoxLayout()
        stop_layout.addWidget(QLabel('停止位:'))
        self.stop_combo = QComboBox()
        self.stop_combo.addItems(['1', '1.5', '2'])
        self.stop_combo.setCurrentText('1')
        stop_layout.addWidget(self.stop_combo)
        settings_layout.addLayout(stop_layout)

        parity_layout = QHBoxLayout()
        parity_layout.addWidget(QLabel('校验位:'))
        self.parity_combo = QComboBox()
        self.parity_combo.addItems(['无', '奇', '偶', 'Mark', 'Space'])
        self.parity_combo.setCurrentText('无')
        parity_layout.addWidget(self.parity_combo)
        settings_layout.addLayout(parity_layout)

        settings_layout.addSpacing(10)

        self.open_btn = QPushButton('打开串口')
        self.open_btn.clicked.connect(self.toggle_serial)
        settings_layout.addWidget(self.open_btn)

        settings_layout.addSpacing(10)

        protocol_layout = QHBoxLayout()
        protocol_layout.addWidget(QLabel('协议:'))
        self.protocol_combo = QComboBox()
        self.protocol_combo.currentTextChanged.connect(self.on_protocol_changed)
        protocol_layout.addWidget(self.protocol_combo)
        settings_layout.addLayout(protocol_layout)

        settings_layout.addSpacing(10)
        
        auto_save_layout = QHBoxLayout()
        self.auto_save_check = QCheckBox('自动保存CSV')
        self.auto_save_check.stateChanged.connect(self.toggle_auto_save)
        auto_save_layout.addWidget(self.auto_save_check)
        settings_layout.addLayout(auto_save_layout)
        
        auto_save_btn_layout = QHBoxLayout()
        self.auto_save_path_btn = QPushButton('选择保存路径')
        self.auto_save_path_btn.clicked.connect(self.select_auto_save_path)
        auto_save_btn_layout.addWidget(self.auto_save_path_btn)
        settings_layout.addLayout(auto_save_btn_layout)

        settings_layout.addSpacing(10)

        command_btn = QPushButton('快捷指令')
        command_btn.clicked.connect(self.open_quick_commands)
        settings_layout.addWidget(command_btn)

        settings_layout.addSpacing(10)

        self.clear_btn = QPushButton('清空接收区')
        self.clear_btn.clicked.connect(lambda: self.receive_text.clear())
        settings_layout.addWidget(self.clear_btn)

        self.save_btn = QPushButton('保存日志')
        self.save_btn.clicked.connect(self.save_log)
        settings_layout.addWidget(self.save_btn)

        settings_layout.addStretch()
        parent_layout.addWidget(settings_group, stretch=1)

    def create_transceiver_panel(self, parent_layout):
        """创建收发面板"""
        transceiver_group = QGroupBox('数据收发')
        transceiver_layout = QVBoxLayout(transceiver_group)
        transceiver_layout.setSpacing(10)
        
        content_layout = QHBoxLayout()
        
        left_panel = QVBoxLayout()
        
        receive_label = QLabel('接收区')
        font = receive_label.font()
        font.setBold(True)
        receive_label.setFont(font)
        left_panel.addWidget(receive_label)

        self.receive_text = QTextEdit()
        self.receive_text.setReadOnly(True)
        left_panel.addWidget(self.receive_text)

        send_label = QLabel('发送区')
        font = send_label.font()
        font.setBold(True)
        send_label.setFont(font)
        left_panel.addWidget(send_label)

        self.send_text = QTextEdit()
        self.send_text.setMaximumHeight(100)
        left_panel.addWidget(self.send_text)

        send_control_layout = QHBoxLayout()
        self.send_btn = QPushButton('发送')
        self.send_btn.clicked.connect(self.send_data)
        send_control_layout.addWidget(self.send_btn)

        self.timer_check = QCheckBox('定时发送')
        self.timer_check.stateChanged.connect(self.toggle_timer)
        send_control_layout.addWidget(self.timer_check)

        self.timer_spin = QSpinBox()
        self.timer_spin.setRange(10, 99999)
        self.timer_spin.setValue(1000)
        self.timer_spin.setSuffix(' ms')
        send_control_layout.addWidget(self.timer_spin)

        send_control_layout.addStretch()
        left_panel.addLayout(send_control_layout)
        
        content_layout.addLayout(left_panel, stretch=2)
        
        right_panel = QVBoxLayout()
        parse_label = QLabel('解析数据')
        font = parse_label.font()
        font.setBold(True)
        parse_label.setFont(font)
        right_panel.addWidget(parse_label)
        
        self.parse_text = QTextEdit()
        self.parse_text.setReadOnly(True)
        right_panel.addWidget(self.parse_text)
        
        realtime_label = QLabel('实时数据')
        font = realtime_label.font()
        font.setBold(True)
        realtime_label.setFont(font)
        right_panel.addWidget(realtime_label)
        
        self.realtime_text = QTextEdit()
        self.realtime_text.setReadOnly(True)
        self.realtime_text.setMaximumHeight(200)
        right_panel.addWidget(self.realtime_text)
        
        content_layout.addLayout(right_panel, stretch=1)
        
        transceiver_layout.addLayout(content_layout)

        parent_layout.addWidget(transceiver_group, stretch=3)

    def connect_signals(self):
        """连接信号和槽"""
        self.serial_manager.port_opened.connect(self.on_port_opened)
        self.serial_manager.port_closed.connect(self.on_port_closed)
        self.serial_manager.data_received.connect(self.on_data_received)
        self.serial_manager.error_occurred.connect(self.on_error)

    def refresh_ports(self):
        """刷新可用串口"""
        self.port_combo.clear()
        ports = self.serial_manager.get_available_ports()
        for port in ports:
            self.port_combo.addItem(port)

    def toggle_serial(self):
        """打开/关闭串口"""
        if self.serial_manager.is_open:
            self.serial_manager.close_port()
        else:
            self.open_serial()

    def open_serial(self):
        """打开串口"""
        port = self.port_combo.currentText()
        if not port:
            self.show_message('警告', '请先选择串口', 'warning')
            return

        config = SerialConfig(
            port=port,
            baudrate=int(self.baud_combo.currentText()),
            bytesize=int(self.data_combo.currentText()),
            stopbits=self.stop_combo.currentText(),
            parity=self.parity_combo.currentText()
        )
        
        self.serial_manager.open_port(config)

    def on_port_opened(self, port: str):
        """串口打开成功"""
        self.open_btn.setText('关闭串口')
        self.status_dot.set_status(True)
        self.status_text.setText('已连接')
        self.show_message('成功', f'串口 {port} 已打开', 'success')

    def on_port_closed(self):
        """串口关闭"""
        self.open_btn.setText('打开串口')
        self.status_dot.set_status(False)
        self.status_text.setText('未连接')
        self.show_message('提示', '串口已关闭', 'info')

    def on_data_received(self, data: bytes):
        """接收到数据"""
        timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        
        formatted = self.data_parser.parse_data(data)
        if formatted:
            self.receive_text.insertPlainText(f'[{timestamp}] {formatted}\n')
            self.receive_text.verticalScrollBar().setValue(
                self.receive_text.verticalScrollBar().maximum()
            )
        
        parsed_raw = self.data_parser.parse_data_raw(data)
        if parsed_raw:
            self.latest_parsed_data = parsed_raw
            self.update_parse_display(parsed_raw, timestamp)
            self.update_realtime_display(parsed_raw)

    def update_parse_display(self, parsed_data, timestamp):
        """更新解析数据显示"""
        if isinstance(parsed_data, dict):
            display_text = f'[{timestamp}]\n'
            display_text += '='*50 + '\n'
            display_text += '原始数据解析过程:\n'
            display_text += '='*50 + '\n'
            
            data_type = parsed_data.get('type', '')
            
            if data_type == 'measurement':
                display_text += '📊 测量数据解析:\n'
                display_text += f'   步骤1: 识别为测量数据类型\n'
                
                if 'tdf' in parsed_data:
                    display_text += f'   步骤2: 提取露点温度: {parsed_data["tdf"]}\n'
                    display_text += f'   步骤3: 提取单位: {parsed_data["tdf_unit"]}\n'
                
                if 'tdfatm' in parsed_data:
                    display_text += f'   步骤4: 提取大气压露点: {parsed_data["tdfatm"]}\n'
                    display_text += f'   步骤5: 提取单位: {parsed_data["tdfatm_unit"]}\n'
                
                if 'h2o' in parsed_data:
                    display_text += f'   步骤6: 提取湿度: {parsed_data["h2o"]} ppm\n'
                
                display_text += '   步骤7: 数据验证完成\n'
            
            elif data_type == 'device_info':
                display_text += '🔧 设备信息解析:\n'
                display_text += f'   步骤1: 识别为设备信息类型\n'
                
                if 'model' in parsed_data:
                    display_text += f'   步骤2: 提取型号: {parsed_data["model"]}\n'
                
                if 'version' in parsed_data:
                    display_text += f'   步骤3: 提取版本: {parsed_data["version"]}\n'
                
                if 'serial_number' in parsed_data:
                    display_text += f'   步骤4: 提取序列号: {parsed_data["serial_number"]}\n'
                
                display_text += '   步骤5: 数据验证完成\n'
            
            elif data_type == 'command_response':
                display_text += '📋 命令响应解析:\n'
                display_text += f'   步骤1: 识别为命令响应类型\n'
                
                if 'responses' in parsed_data:
                    display_text += f'   步骤2: 找到 {len(parsed_data["responses"])} 个响应项\n'
                    for i, resp in enumerate(parsed_data['responses']):
                        display_text += f'   步骤{i+3}: 提取 "{resp["key"]}": {resp["value"]}\n'
                
                display_text += '   步骤完成\n'
            
            display_text += '='*50 + '\n\n'
            self.parse_text.insertPlainText(display_text)
            self.parse_text.verticalScrollBar().setValue(
                self.parse_text.verticalScrollBar().maximum()
            )
    
    def update_realtime_display(self, parsed_data):
        """更新实时数据显示"""
        if isinstance(parsed_data, dict):
            data_type = parsed_data.get('type', '')
            display_text = ''
            
            if data_type == 'measurement':
                display_text += '📊 实时测量数据\n'
                display_text += '─'*30 + '\n'
                
                if 'tdf' in parsed_data:
                    display_text += f'露点温度: {parsed_data["tdf"]:.2f} °{parsed_data["tdf_unit"]}\n'
                
                if 'tdfatm' in parsed_data:
                    display_text += f'大气压露点: {parsed_data["tdfatm"]:.2f} °{parsed_data["tdfatm_unit"]}\n'
                
                if 'h2o' in parsed_data:
                    display_text += f'湿度: {parsed_data["h2o"]:.0f} ppm\n'
                
                if 'tdf' in parsed_data and parsed_data['tdf_unit'] == 'F':
                    tdf_c = (parsed_data['tdf'] - 32) * 5/9
                    display_text += f'露点(转换): {tdf_c:.2f} °C\n'
                
                if 'tdfatm' in parsed_data and parsed_data['tdfatm_unit'] == 'F':
                    tdfatm_c = (parsed_data['tdfatm'] - 32) * 5/9
                    display_text += f'大气压露点(转换): {tdfatm_c:.2f} °C\n'
            
            elif data_type == 'device_info':
                display_text += '🔧 设备信息\n'
                display_text += '─'*30 + '\n'
                
                if 'model' in parsed_data:
                    display_text += f'型号: {parsed_data["model"]}\n'
                
                if 'version' in parsed_data:
                    display_text += f'版本: {parsed_data["version"]}\n'
                
                if 'serial_number' in parsed_data:
                    display_text += f'序列号: {parsed_data["serial_number"]}\n'
                
                if 'sensor_model' in parsed_data:
                    display_text += f'传感器型号: {parsed_data["sensor_model"]}\n'
                
                if 'cal_date' in parsed_data:
                    display_text += f'校准日期: {parsed_data["cal_date"]}\n'
            
            elif data_type == 'command_response':
                display_text += '📋 命令响应\n'
                display_text += '─'*30 + '\n'
                
                if 'responses' in parsed_data:
                    for resp in parsed_data['responses']:
                        display_text += f'{resp["key"]}: {resp["value"]}\n'
            
            elif data_type == 'raw':
                display_text += '📄 原始数据\n'
                display_text += '─'*30 + '\n'
                display_text += f'{parsed_data.get("raw_data", "")}\n'
            
            elif data_type == 'error':
                display_text += '❌ 解析错误\n'
                display_text += '─'*30 + '\n'
                display_text += f'错误: {parsed_data.get("error", "")}\n'
                display_text += f'原始数据: {parsed_data.get("raw_data", "")}\n'
            
            if display_text:
                self.realtime_text.clear()
                self.realtime_text.setPlainText(display_text)
    
    def on_error(self, error_msg: str):
        """错误处理"""
        self.show_message('错误', error_msg, 'error')

    def send_data(self):
        """发送数据"""
        if not self.serial_manager.is_open:
            self.show_message('警告', '请先打开串口', 'warning')
            return

        text = self.send_text.toPlainText()
        if not text:
            return

        data = self.data_parser.encode_data(text)
        if data:
            self.serial_manager.send_data(data)
        else:
            self.show_message('警告', '数据编码失败', 'warning')

    def toggle_timer(self, state):
        """切换定时器开关"""
        if state == Qt.CheckState.Checked:
            if not self.serial_manager.is_open:
                self.timer_check.setChecked(False)
                self.show_message('警告', '请先打开串口', 'warning')
                return
            interval = self.timer_spin.value()
            self.timer.start(interval)
        else:
            self.timer.stop()

    def send_periodic_data(self):
        """定时发送数据"""
        self.send_data()

    def save_log(self):
        """保存日志到文件"""
        text = self.receive_text.toPlainText()
        if not text:
            self.show_message('警告', '接收区为空', 'warning')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, '保存日志', '', '文本文件 (*.txt);;所有文件 (*.*)'
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.show_message('成功', '日志保存成功', 'success')
            except Exception as e:
                self.show_message('错误', f'保存失败: {str(e)}', 'error')

    def toggle_auto_save(self, state):
        """切换自动保存"""
        if state == Qt.CheckState.Checked:
            if not self.auto_save_path:
                self.auto_save_check.setChecked(False)
                self.show_message('警告', '请先选择保存路径', 'warning')
                return
            self.auto_save_enabled = True
            self.auto_save_timer.start(5000)
            self.show_message('提示', '自动保存已开启', 'info')
        else:
            self.auto_save_enabled = False
            self.auto_save_timer.stop()
            self.show_message('提示', '自动保存已关闭', 'info')

    def select_auto_save_path(self):
        """选择自动保存路径"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, '选择自动保存路径', '', 'CSV文件 (*.csv)'
        )
        if file_path:
            self.auto_save_path = file_path
            self.show_message('成功', f'保存路径已设置: {file_path}', 'success')

    def auto_save_csv(self):
        """自动保存为CSV"""
        if not self.auto_save_enabled or not self.auto_save_path:
            return
        
        text = self.receive_text.toPlainText()
        if not text:
            return
        
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(self.auto_save_path, 'a', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([timestamp, text])
        except Exception as e:
            self.show_message('错误', f'自动保存失败: {str(e)}', 'error')

    def open_quick_commands(self):
        """打开快捷指令面板"""
        dialog = QuickCommandListDialog(self)
        dialog.set_commands(self.quick_commands)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.quick_commands = dialog.get_commands()
            if dialog.selected_command:
                self.send_text.setPlainText(dialog.selected_command)
                self.send_data()

    def on_protocol_changed(self, protocol_name: str):
        """协议切换"""
        self.data_parser.set_active_plugin(protocol_name)

    def update_protocol_combo(self):
        """更新协议下拉框"""
        self.protocol_combo.clear()
        self.protocol_combo.addItems(self.data_parser.get_plugin_names())

    def show_message(self, title: str, content: str, type: str):
        """显示消息提示"""
        from PyQt5.QtWidgets import QMessageBox
        
        if type == 'success':
            QMessageBox.information(self, title, content)
        elif type == 'warning':
            QMessageBox.warning(self, title, content)
        elif type == 'error':
            QMessageBox.critical(self, title, content)
        else:
            QMessageBox.information(self, title, content)
