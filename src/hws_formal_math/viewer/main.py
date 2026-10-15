"""桌面查看器入口"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTextEdit, QVBoxLayout, QWidget, QPushButton
from PySide6.QtCore import Qt


class ViewerWindow(QMainWindow):
    """桌面查看器主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HWS-formal-math-navigator 查看器")
        self.resize(800, 600)
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 命题输入
        self.proposition_input = QTextEdit()
        self.proposition_input.setPlaceholderText("输入数学命题...")
        layout.addWidget(self.proposition_input)
        
        # 搜索按钮
        self.search_button = QPushButton("检索定理")
        layout.addWidget(self.search_button)
        
        # 结果展示
        self.result_view = QTextEdit()
        self.result_view.setReadOnly(True)
        layout.addWidget(self.result_view)
        
        central_widget.setLayout(layout)


def main():
    """GUI 入口"""
    app = QApplication(sys.argv)
    window = ViewerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
