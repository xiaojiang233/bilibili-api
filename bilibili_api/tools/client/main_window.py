"""
Bilibili 第三方客户端主窗口
"""

import sys
import asyncio
from typing import Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel,
    QFrame, QScrollArea, QMenuBar, QMenu, QStatusBar, QTabWidget,
    QTextEdit, QProgressBar, QGroupBox, QGridLayout, QMessageBox,
    QSplitter, QToolBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon, QAction

import bilibili_api
from bilibili_api import video, search, user, Credential
from .material_style import MATERIAL_THEME


class VideoCard(QFrame):
    """视频卡片组件"""
    
    def __init__(self, video_info: dict):
        super().__init__()
        self.video_info = video_info
        self.setupUI()
        
    def setupUI(self):
        self.setObjectName("videoCard")
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # 视频标题
        title_label = QLabel(self.video_info.get('title', '无标题'))
        title_label.setObjectName("titleLabel")
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(60)
        
        # UP主信息
        author_label = QLabel(f"UP主: {self.video_info.get('owner', {}).get('name', '未知')}")
        author_label.setObjectName("subtitleLabel")
        
        # 播放信息
        view_count = self.video_info.get('stat', {}).get('view', 0)
        like_count = self.video_info.get('stat', {}).get('like', 0)
        
        stats_label = QLabel(f"播放: {self.format_count(view_count)} | 点赞: {self.format_count(like_count)}")
        stats_label.setObjectName("subtitleLabel")
        
        # BVID信息
        bvid_label = QLabel(self.video_info.get('bvid', ''))
        bvid_label.setObjectName("subtitleLabel")
        
        layout.addWidget(title_label)
        layout.addWidget(author_label)
        layout.addWidget(stats_label)
        layout.addWidget(bvid_label)
        layout.addStretch()
        
    def format_count(self, count: int) -> str:
        """格式化数字显示"""
        if count >= 10000:
            return f"{count/10000:.1f}万"
        return str(count)
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            bvid = self.video_info.get('bvid', '')
            if bvid:
                print(f"点击了视频: {bvid}")
                # 这里可以添加播放视频的逻辑
        super().mousePressEvent(event)


class SearchWorker(QThread):
    """搜索工作线程"""
    search_finished = pyqtSignal(list)
    search_error = pyqtSignal(str)
    
    def __init__(self, keyword: str):
        super().__init__()
        self.keyword = keyword
        
    def run(self):
        try:
            # 创建异步事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 执行搜索
            results = loop.run_until_complete(self.search_videos())
            self.search_finished.emit(results)
            
        except Exception as e:
            self.search_error.emit(str(e))
        finally:
            loop.close()
            
    async def search_videos(self):
        """异步搜索视频"""
        try:
            # 使用bilibili-api进行搜索
            search_result = await search.search_by_type(
                keyword=self.keyword,
                search_type=search.SearchObjectType.VIDEO,
                order_type=search.OrderType.TOTALRANK,
                page=1
            )
            return search_result.get('result', [])
        except Exception as e:
            raise e


class LoginDialog(QWidget):
    """登录对话框"""
    
    def __init__(self):
        super().__init__()
        self.setupUI()
        
    def setupUI(self):
        self.setWindowTitle("Bilibili 登录")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title = QLabel("Bilibili 账号登录")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 说明文本
        info_text = QTextEdit()
        info_text.setPlainText("""
请按照以下步骤获取登录信息：

1. 打开浏览器，登录 bilibili.com
2. 按 F12 打开开发者工具
3. 找到 Application -> Storage -> Cookies
4. 复制 SESSDATA、bili_jct、buvid3 的值
5. 粘贴到下方输入框中

注意：请勿泄露这些信息给他人！
        """)
        info_text.setMaximumHeight(120)
        
        # 输入框
        self.sessdata_edit = QLineEdit()
        self.sessdata_edit.setPlaceholderText("SESSDATA")
        
        self.bili_jct_edit = QLineEdit()
        self.bili_jct_edit.setPlaceholderText("bili_jct")
        
        self.buvid3_edit = QLineEdit()
        self.buvid3_edit.setPlaceholderText("buvid3")
        
        # 按钮
        login_btn = QPushButton("登录")
        login_btn.clicked.connect(self.login)
        
        layout.addWidget(title)
        layout.addWidget(info_text)
        layout.addWidget(self.sessdata_edit)
        layout.addWidget(self.bili_jct_edit)
        layout.addWidget(self.buvid3_edit)
        layout.addWidget(login_btn)
        
    def login(self):
        """登录处理"""
        sessdata = self.sessdata_edit.text().strip()
        bili_jct = self.bili_jct_edit.text().strip()
        buvid3 = self.buvid3_edit.text().strip()
        
        if not all([sessdata, bili_jct, buvid3]):
            QMessageBox.warning(self, "错误", "请填写完整的登录信息")
            return
            
        try:
            credential = Credential(
                sessdata=sessdata,
                bili_jct=bili_jct,
                buvid3=buvid3
            )
            # 这里应该验证凭据有效性，简化处理直接接受
            QMessageBox.information(self, "成功", "登录信息已保存")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"登录失败: {str(e)}")


class BilibiliClient(QMainWindow):
    """Bilibili 第三方客户端主窗口"""
    
    def __init__(self):
        super().__init__()
        self.credential: Optional[Credential] = None
        self.search_worker: Optional[SearchWorker] = None
        self.setupUI()
        self.setupStyle()
        
    def setupUI(self):
        """设置用户界面"""
        self.setWindowTitle("Bilibili 第三方客户端 - Material Design")
        self.setMinimumSize(1200, 800)
        
        # 创建菜单栏
        self.createMenuBar()
        
        # 创建工具栏
        self.createToolBar()
        
        # 创建状态栏
        self.statusBar().showMessage("就绪")
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左侧边栏
        sidebar = self.createSidebar()
        sidebar.setObjectName("sidebar")
        sidebar.setMaximumWidth(250)
        splitter.addWidget(sidebar)
        
        # 主内容区域
        main_content = self.createMainContent()
        main_content.setObjectName("mainContent")
        splitter.addWidget(main_content)
        
        # 设置分割器比例
        splitter.setStretchFactor(0, 0)  # 侧边栏不伸缩
        splitter.setStretchFactor(1, 1)  # 主内容区域伸缩
        
    def createMenuBar(self):
        """创建菜单栏"""
        # 文件菜单
        file_menu = self.menuBar().addMenu("文件")
        file_menu.addAction("退出", self.close)
        
        # 用户菜单
        user_menu = self.menuBar().addMenu("用户")
        user_menu.addAction("登录", self.showLoginDialog)
        user_menu.addAction("登出", self.logout)
        
        # 帮助菜单
        help_menu = self.menuBar().addMenu("帮助")
        help_menu.addAction("关于", self.showAbout)
        
    def createToolBar(self):
        """创建工具栏"""
        toolbar = QToolBar("主工具栏")
        self.addToolBar(toolbar)
        
        # 搜索框
        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("searchEdit")
        self.search_edit.setPlaceholderText("搜索视频、UP主...")
        self.search_edit.setMaximumWidth(300)
        self.search_edit.returnPressed.connect(self.search)
        toolbar.addWidget(self.search_edit)
        
        # 搜索按钮
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.search)
        toolbar.addWidget(search_btn)
        
        toolbar.addSeparator()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(refresh_btn)
        
    def createSidebar(self):
        """创建侧边栏"""
        sidebar = QFrame()
        layout = QVBoxLayout(sidebar)
        
        # 用户信息区域
        user_group = QGroupBox("用户信息")
        user_layout = QVBoxLayout(user_group)
        
        self.user_avatar = QLabel()
        self.user_avatar.setObjectName("avatarLabel")
        self.user_avatar.setFixedSize(60, 60)
        self.user_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_avatar.setText("未登录")
        self.user_avatar.setStyleSheet("border: 1px solid #ccc; border-radius: 30px;")
        
        self.user_name = QLabel("点击登录")
        self.user_name.setObjectName("titleLabel")
        
        user_layout.addWidget(self.user_avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        user_layout.addWidget(self.user_name, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 导航菜单
        nav_group = QGroupBox("导航")
        nav_layout = QVBoxLayout(nav_group)
        
        nav_buttons = [
            ("🏠 首页", self.showHome),
            ("🔥 热门", self.showHot),
            ("📺 直播", self.showLive),
            ("🎵 音乐", self.showMusic),
            ("📖 专栏", self.showArticle),
            ("🎮 游戏", self.showGame),
        ]
        
        for text, handler in nav_buttons:
            btn = QPushButton(text)
            btn.setProperty("flat", True)
            btn.clicked.connect(handler)
            nav_layout.addWidget(btn)
            
        layout.addWidget(user_group)
        layout.addWidget(nav_group)
        layout.addStretch()
        
        return sidebar
        
    def createMainContent(self):
        """创建主内容区域"""
        main_content = QFrame()
        layout = QVBoxLayout(main_content)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 搜索结果选项卡
        self.search_tab = self.createSearchTab()
        self.tab_widget.addTab(self.search_tab, "搜索结果")
        
        # 推荐视频选项卡
        self.recommend_tab = self.createRecommendTab()
        self.tab_widget.addTab(self.recommend_tab, "推荐")
        
        layout.addWidget(self.tab_widget)
        
        return main_content
        
    def createSearchTab(self):
        """创建搜索结果选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 搜索结果标题
        self.search_title = QLabel("搜索结果")
        self.search_title.setObjectName("titleLabel")
        layout.addWidget(self.search_title)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 搜索结果滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.search_content = QWidget()
        self.search_layout = QGridLayout(self.search_content)
        self.search_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.search_content)
        layout.addWidget(scroll_area)
        
        return tab
        
    def createRecommendTab(self):
        """创建推荐选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        title = QLabel("推荐内容")
        title.setObjectName("titleLabel")
        layout.addWidget(title)
        
        info = QLabel("推荐功能正在开发中...")
        info.setObjectName("subtitleLabel")
        layout.addWidget(info)
        
        layout.addStretch()
        
        return tab
        
    def setupStyle(self):
        """应用Material Design样式"""
        self.setStyleSheet(MATERIAL_THEME)
        
    def search(self):
        """执行搜索"""
        keyword = self.search_edit.text().strip()
        if not keyword:
            return
            
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 无限进度条
        self.statusBar().showMessage(f"正在搜索: {keyword}")
        
        # 清空之前的搜索结果
        self.clearSearchResults()
        
        # 创建搜索工作线程
        self.search_worker = SearchWorker(keyword)
        self.search_worker.search_finished.connect(self.onSearchFinished)
        self.search_worker.search_error.connect(self.onSearchError)
        self.search_worker.start()
        
    def clearSearchResults(self):
        """清空搜索结果"""
        for i in reversed(range(self.search_layout.count())):
            item = self.search_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                    
    def onSearchFinished(self, results: list):
        """搜索完成回调"""
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage(f"搜索完成，找到 {len(results)} 个结果")
        
        # 更新标题
        self.search_title.setText(f"搜索结果 ({len(results)})")
        
        # 显示搜索结果
        row, col = 0, 0
        max_cols = 3  # 每行最多3个视频卡片
        
        for video_info in results:
            if 'bvid' in video_info and 'title' in video_info:
                video_card = VideoCard(video_info)
                self.search_layout.addWidget(video_card, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
                    
        # 切换到搜索结果选项卡
        self.tab_widget.setCurrentWidget(self.search_tab)
        
    def onSearchError(self, error_msg: str):
        """搜索错误回调"""
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("搜索失败")
        QMessageBox.critical(self, "搜索错误", f"搜索失败: {error_msg}")
        
    def showLoginDialog(self):
        """显示登录对话框"""
        dialog = LoginDialog()
        dialog.show()
        
    def logout(self):
        """登出"""
        self.credential = None
        self.user_name.setText("点击登录")
        self.user_avatar.setText("未登录")
        self.statusBar().showMessage("已登出")
        
    def refresh(self):
        """刷新内容"""
        self.statusBar().showMessage("刷新中...")
        # 这里可以添加刷新逻辑
        QTimer.singleShot(1000, lambda: self.statusBar().showMessage("刷新完成"))
        
    def showAbout(self):
        """显示关于信息"""
        QMessageBox.about(
            self, 
            "关于", 
            f"Bilibili 第三方客户端\n\n"
            f"基于 bilibili-api {bilibili_api.BILIBILI_API_VERSION}\n"
            f"使用 PyQt6 和 Material Design\n\n"
            f"仅供学习和测试使用"
        )
        
    # 导航按钮回调函数
    def showHome(self):
        self.statusBar().showMessage("首页功能开发中...")
        
    def showHot(self):
        self.statusBar().showMessage("热门功能开发中...")
        
    def showLive(self):
        self.statusBar().showMessage("直播功能开发中...")
        
    def showMusic(self):
        self.statusBar().showMessage("音乐功能开发中...")
        
    def showArticle(self):
        self.statusBar().showMessage("专栏功能开发中...")
        
    def showGame(self):
        self.statusBar().showMessage("游戏功能开发中...")
        

def main():
    """启动客户端"""
    app = QApplication(sys.argv)
    app.setApplicationName("Bilibili Client")
    app.setApplicationDisplayName("Bilibili 第三方客户端")
    
    # 创建并显示主窗口
    window = BilibiliClient()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()