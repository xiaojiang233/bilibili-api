"""
UI组件展示脚本 - 演示Material Design样式
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QGroupBox, QListWidget, QListWidgetItem,
    QProgressBar, QTabWidget, QTextEdit
)
from PyQt6.QtCore import Qt

from bilibili_api.tools.client.material_style import MATERIAL_THEME


class MaterialDesignDemo(QMainWindow):
    """Material Design 组件演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.setupUI()
        self.setStyleSheet(MATERIAL_THEME)
        
    def setupUI(self):
        self.setWindowTitle("Material Design 组件演示")
        self.setMinimumSize(600, 500)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 标题
        title = QLabel("Material Design 组件演示")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 按钮组
        button_group = QGroupBox("按钮样式")
        button_layout = QHBoxLayout(button_group)
        
        normal_btn = QPushButton("普通按钮")
        flat_btn = QPushButton("扁平按钮")
        flat_btn.setProperty("flat", True)
        disabled_btn = QPushButton("禁用按钮")
        disabled_btn.setEnabled(False)
        
        button_layout.addWidget(normal_btn)
        button_layout.addWidget(flat_btn)
        button_layout.addWidget(disabled_btn)
        
        # 输入框组
        input_group = QGroupBox("输入框样式")
        input_layout = QVBoxLayout(input_group)
        
        normal_edit = QLineEdit()
        normal_edit.setPlaceholderText("普通输入框")
        
        search_edit = QLineEdit()
        search_edit.setObjectName("searchEdit")
        search_edit.setPlaceholderText("搜索框样式")
        
        input_layout.addWidget(normal_edit)
        input_layout.addWidget(search_edit)
        
        # 进度条
        progress_group = QGroupBox("进度条")
        progress_layout = QVBoxLayout(progress_group)
        
        progress = QProgressBar()
        progress.setValue(65)
        progress_layout.addWidget(progress)
        
        # 列表
        list_group = QGroupBox("列表样式")
        list_layout = QVBoxLayout(list_group)
        
        list_widget = QListWidget()
        for i in range(3):
            item = QListWidgetItem(f"列表项 {i + 1}")
            list_widget.addItem(item)
        
        list_layout.addWidget(list_widget)
        
        layout.addWidget(button_group)
        layout.addWidget(input_group)
        layout.addWidget(progress_group)
        layout.addWidget(list_group)


def demo_material_design():
    """演示Material Design组件"""
    app = QApplication(sys.argv)
    
    window = MaterialDesignDemo()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(demo_material_design())