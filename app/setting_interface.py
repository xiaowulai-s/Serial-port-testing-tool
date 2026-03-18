from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont


class SettingInterface(QWidget):
    """设置页面"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName('SettingInterface')

        self.init_ui()

    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel('设置')
        font = title_label.font()
        font.setBold(True)
        font.setPointSize(16)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        info_label = QLabel('设置页面正在开发中...')
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        layout.addStretch()
