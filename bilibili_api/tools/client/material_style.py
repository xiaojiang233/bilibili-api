"""
Material Design 风格的 QSS 样式表
"""

MATERIAL_THEME = """
/* 主窗口样式 */
QMainWindow {
    background-color: #fafafa;
    color: #212121;
}

/* 工具栏样式 */
QToolBar {
    background-color: #2196f3;
    color: white;
    border: none;
    spacing: 3px;
    padding: 8px;
}

QToolBar::handle {
    background-color: #1976d2;
    width: 3px;
    margin: 2px 0;
}

/* 按钮样式 */
QPushButton {
    background-color: #2196f3;
    color: white;
    border: none;
    padding: 10px 16px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    min-width: 64px;
}

QPushButton:hover {
    background-color: #1976d2;
    box-shadow: 0px 2px 4px rgba(0,0,0,0.2);
}

QPushButton:pressed {
    background-color: #0d47a1;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

/* 扁平按钮样式 */
QPushButton[flat="true"] {
    background-color: transparent;
    color: #2196f3;
}

QPushButton[flat="true"]:hover {
    background-color: rgba(33, 150, 243, 0.12);
}

/* 输入框样式 */
QLineEdit {
    border: none;
    border-bottom: 2px solid #e0e0e0;
    background-color: transparent;
    padding: 8px 0px 8px 0px;
    font-size: 16px;
    color: #212121;
}

QLineEdit:focus {
    border-bottom: 2px solid #2196f3;
}

/* 搜索框样式 */
QLineEdit#searchEdit {
    border: 1px solid #e0e0e0;
    border-radius: 20px;
    padding: 8px 16px;
    background-color: #f5f5f5;
}

QLineEdit#searchEdit:focus {
    border: 1px solid #2196f3;
    background-color: white;
}

/* 标签样式 */
QLabel {
    color: #212121;
    font-size: 14px;
}

QLabel#titleLabel {
    font-size: 20px;
    font-weight: 500;
    color: #212121;
}

QLabel#subtitleLabel {
    font-size: 14px;
    color: #757575;
}

/* 滚动条样式 */
QScrollBar:vertical {
    background: #f5f5f5;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #bdbdbd;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #9e9e9e;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

/* 列表视图样式 */
QListWidget {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    outline: none;
}

QListWidget::item {
    border-bottom: 1px solid #e0e0e0;
    padding: 12px;
}

QListWidget::item:selected {
    background-color: #e3f2fd;
    color: #1976d2;
}

QListWidget::item:hover {
    background-color: #f5f5f5;
}

/* 菜单栏样式 */
QMenuBar {
    background-color: #2196f3;
    color: white;
    border: none;
}

QMenuBar::item {
    background-color: transparent;
    padding: 8px 16px;
}

QMenuBar::item:selected {
    background-color: #1976d2;
}

QMenuBar::item:pressed {
    background-color: #0d47a1;
}

/* 菜单样式 */
QMenu {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
}

QMenu::item {
    padding: 8px 16px;
}

QMenu::item:selected {
    background-color: #e3f2fd;
    color: #1976d2;
}

/* 状态栏样式 */
QStatusBar {
    background-color: #f5f5f5;
    color: #757575;
    border-top: 1px solid #e0e0e0;
}

/* 选项卡样式 */
QTabWidget::pane {
    border: 1px solid #e0e0e0;
    background-color: white;
}

QTabBar::tab {
    background-color: #f5f5f5;
    color: #757575;
    padding: 12px 16px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: white;
    color: #2196f3;
    border-bottom: 2px solid #2196f3;
}

QTabBar::tab:hover {
    background-color: #eeeeee;
}

/* 分组框样式 */
QGroupBox {
    font-size: 16px;
    font-weight: 500;
    color: #2196f3;
    border: 2px solid #e0e0e0;
    border-radius: 4px;
    margin-top: 1ex;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px;
}

/* 文本编辑器样式 */
QTextEdit {
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    background-color: white;
    color: #212121;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* 进度条样式 */
QProgressBar {
    border: none;
    border-radius: 2px;
    background-color: #e0e0e0;
    text-align: center;
    color: #212121;
}

QProgressBar::chunk {
    background-color: #2196f3;
    border-radius: 2px;
}

/* 视频卡片样式 */
QFrame#videoCard {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin: 4px;
}

QFrame#videoCard:hover {
    border: 1px solid #2196f3;
    box-shadow: 0px 4px 8px rgba(0,0,0,0.1);
}

/* 侧边栏样式 */
QFrame#sidebar {
    background-color: white;
    border-right: 1px solid #e0e0e0;
}

/* 主内容区域样式 */
QFrame#mainContent {
    background-color: #fafafa;
}

/* 用户头像标签 */
QLabel#avatarLabel {
    border-radius: 20px;
    border: 2px solid #e0e0e0;
}

/* 卡片阴影效果 */
QFrame[shadow="true"] {
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
}
"""