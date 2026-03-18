from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QStackedWidget, QPushButton, QLabel)
from PyQt5.QtGui import QFont
from app.home_interface import HomeInterface
from app.setting_interface import SettingInterface


class MainWindow(QMainWindow):
    """主窗口 - 简化版本，避免兼容性问题"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        self.resize(1100, 750)
        self.setWindowTitle('串口测试工具')
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)
        
        self.stacked_widget = QStackedWidget()
        self.home_interface = HomeInterface()
        self.setting_interface = SettingInterface()
        self.stacked_widget.addWidget(self.home_interface)
        self.stacked_widget.addWidget(self.setting_interface)
        main_layout.addWidget(self.stacked_widget, stretch=1)
        
        self.current_index = 0
        self.update_nav_buttons()

    def create_sidebar(self):
        """创建侧边栏"""
        sidebar = QWidget()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet("""
            QWidget {
                background-color: #f3f3f3;
                border-right: 1px solid #d0d0d0;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 20, 10, 20)
        
        title_label = QLabel('串口测试工具')
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        layout.addSpacing(20)
        
        self.home_btn = QPushButton('🏠  首页')
        self.home_btn.setCheckable(True)
        self.home_btn.clicked.connect(lambda: self.switch_page(0))
        self.home_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px 15px;
                border: none;
                border-radius: 6px;
                background-color: transparent;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
            QPushButton:checked {
                background-color: #0078d4;
                color: white;
            }
        """)
        layout.addWidget(self.home_btn)
        
        self.setting_btn = QPushButton('⚙️  设置')
        self.setting_btn.setCheckable(True)
        self.setting_btn.clicked.connect(lambda: self.switch_page(1))
        self.setting_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px 15px;
                border: none;
                border-radius: 6px;
                background-color: transparent;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
            QPushButton:checked {
                background-color: #0078d4;
                color: white;
            }
        """)
        layout.addWidget(self.setting_btn)
        
        layout.addStretch()
        
        return sidebar

    def switch_page(self, index):
        """切换页面"""
        self.current_index = index
        self.stacked_widget.setCurrentIndex(index)
        self.update_nav_buttons()

    def update_nav_buttons(self):
        """更新导航按钮状态"""
        self.home_btn.setChecked(self.current_index == 0)
        self.setting_btn.setChecked(self.current_index == 1)
