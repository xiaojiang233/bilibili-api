"""
Bilibili 第三方客户端主窗口
"""

import sys
import asyncio
import random
from typing import Optional, List
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QLabel,
    QFrame, QScrollArea, QMenuBar, QMenu, QStatusBar, QTabWidget,
    QTextEdit, QProgressBar, QGroupBox, QGridLayout, QMessageBox,
    QSplitter, QToolBar, QDialog, QComboBox, QSpinBox, QSlider
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QByteArray, QUrl, QPoint, QRectF, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPixmap, QFont, QIcon, QAction, QDesktopServices, QPainter, QColor, QPen
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget

import bilibili_api
from bilibili_api import video, search, user, Credential, hot, dynamic, live, favorite_list, comment, Danmaku
from .material_style import MATERIAL_THEME


class ImageLoader(QLabel):
    """异步图片加载器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self.on_image_loaded)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText("加载中...")
        
    def load_url(self, url: str):
        """从URL加载图片"""
        if url:
            request = QNetworkRequest(QUrl(url))
            self.manager.get(request)
    
    def on_image_loaded(self, reply: QNetworkReply):
        """图片加载完成"""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(scaled_pixmap)
            else:
                self.setText("加载失败")
        else:
            self.setText("加载失败")
        reply.deleteLater()


class VideoCard(QFrame):
    """视频卡片组件"""
    
    clicked = pyqtSignal(dict)  # 添加点击信号
    
    def __init__(self, video_info: dict):
        super().__init__()
        self.video_info = video_info
        self.setupUI()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def setupUI(self):
        self.setObjectName("videoCard")
        self.setFixedSize(300, 280)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # 视频封面
        self.thumbnail = ImageLoader(self)
        self.thumbnail.setFixedSize(276, 155)
        self.thumbnail.setStyleSheet("background-color: #e0e0e0; border-radius: 4px;")
        
        # 加载封面图片
        pic_url = self.video_info.get('pic', '') or self.video_info.get('cover', '')
        if pic_url:
            # 添加 https: 如果URL以 // 开头
            if pic_url.startswith('//'):
                pic_url = 'https:' + pic_url
            self.thumbnail.load_url(pic_url)
        
        # 视频标题
        title_label = QLabel(self.video_info.get('title', '无标题'))
        title_label.setObjectName("titleLabel")
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(45)
        title_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        
        # UP主信息
        author_name = self.video_info.get('owner', {}).get('name', '') or self.video_info.get('author', '未知')
        author_label = QLabel(f"UP主: {author_name}")
        author_label.setObjectName("subtitleLabel")
        
        # 播放信息
        view_count = self.video_info.get('stat', {}).get('view', 0) or self.video_info.get('play', 0)
        like_count = self.video_info.get('stat', {}).get('like', 0)
        
        stats_label = QLabel(f"▶ {self.format_count(view_count)} | 👍 {self.format_count(like_count)}")
        stats_label.setObjectName("subtitleLabel")
        
        layout.addWidget(self.thumbnail)
        layout.addWidget(title_label)
        layout.addWidget(author_label)
        layout.addWidget(stats_label)
        layout.addStretch()
        
    def format_count(self, count: int) -> str:
        """格式化数字显示"""
        if count >= 10000:
            return f"{count/10000:.1f}万"
        return str(count)
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.video_info)
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


class HotVideosWorker(QThread):
    """热门视频工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.fetch_hot_videos())
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
            
    async def fetch_hot_videos(self):
        """获取热门视频"""
        try:
            hot_videos = await hot.get_hot_videos()
            return hot_videos.get('list', [])
        except Exception as e:
            raise e


class RecommendVideosWorker(QThread):
    """推荐视频工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.fetch_recommend_videos())
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
            
    async def fetch_recommend_videos(self):
        """获取推荐视频"""
        try:
            from bilibili_api import homepage
            recommend_data = await homepage.get_videos()
            return recommend_data.get('item', [])
        except Exception as e:
            raise e


class VideoDetailWorker(QThread):
    """视频详情工作线程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, bvid: str, credential: Optional[Credential] = None):
        super().__init__()
        self.bvid = bvid
        self.credential = credential
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.fetch_video_detail())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
            
    async def fetch_video_detail(self):
        """获取视频详情"""
        try:
            v = video.Video(bvid=self.bvid, credential=self.credential)
            info = await v.get_info()
            return info
        except Exception as e:
            raise e


class LiveRoomsWorker(QThread):
    """直播间工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.fetch_live_rooms())
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
            
    async def fetch_live_rooms(self):
        """获取推荐直播间"""
        try:
            from bilibili_api import live_area
            # 获取全部分区的推荐直播间
            rooms = await live_area.get_list_by_area(area_id=0, page=1)
            return rooms.get('list', [])
        except Exception as e:
            raise e


class UserDynamicsWorker(QThread):
    """用户动态工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, uid: int, credential: Optional[Credential] = None):
        super().__init__()
        self.uid = uid
        self.credential = credential
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.fetch_dynamics())
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
            
    async def fetch_dynamics(self):
        """获取用户动态"""
        try:
            u = user.User(uid=self.uid, credential=self.credential)
            dynamics_data = await u.get_dynamics()
            items = dynamics_data.get('items', [])
            return items
        except Exception as e:
            raise e


class AllDynamicsWorker(QThread):
    """全站动态工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.fetch_dynamics())
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
            
    async def fetch_dynamics(self):
        """获取全站动态"""
        try:
            # 获取全站动态
            from bilibili_api import homepage
            dynamics_data = await homepage.get_videos()
            items = dynamics_data.get('item', [])
            # 将视频格式转为简单动态格式
            dynamics = []
            for item in items:
                dynamic_item = {
                    'id_str': str(item.get('id', '')),
                    'type': 'DYNAMIC_TYPE_AV',
                    'modules': {
                        'module_dynamic': {
                            'desc': {
                                'text': item.get('title', '')
                            }
                        },
                        'module_author': {
                            'name': item.get('owner', {}).get('name', '未知')
                        },
                        'module_stat': {
                            'like': {'count': item.get('stat', {}).get('like', 0)},
                            'reply': {'count': item.get('stat', {}).get('reply', 0)}
                        }
                    }
                }
                dynamics.append(dynamic_item)
            return dynamics
        except Exception as e:
            raise e


class VideoPlayUrlWorker(QThread):
    """视频播放地址工作线程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, bvid: str, cid: int, credential: Optional[Credential] = None):
        super().__init__()
        self.bvid = bvid
        self.cid = cid
        self.credential = credential
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.fetch_play_url())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
            
    async def fetch_play_url(self):
        """获取视频播放地址"""
        try:
            v = video.Video(bvid=self.bvid, credential=self.credential)
            # 获取视频下载/播放URL
            play_info = await v.get_download_url(cid=self.cid)
            return play_info
        except Exception as e:
            raise e


class DanmakuWorker(QThread):
    """弹幕工作线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, bvid: str, cid: int, credential: Optional[Credential] = None):
        super().__init__()
        self.bvid = bvid
        self.cid = cid
        self.credential = credential
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.fetch_danmakus())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
            
    async def fetch_danmakus(self):
        """获取弹幕"""
        try:
            v = video.Video(bvid=self.bvid, credential=self.credential)
            # 获取弹幕列表
            danmakus = await v.get_danmakus(cid=self.cid)
            return danmakus
        except Exception as e:
            raise e


class DanmakuLabel(QLabel):
    """弹幕标签组件"""
    
    def __init__(self, text: str, color: QColor, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                color: {color.name()};
                background-color: transparent;
                font-size: 20px;
                font-weight: bold;
                padding: 2px 5px;
            }}
        """)
        # 设置文字描边效果
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
    def paintEvent(self, event):
        """绘制带描边的文字"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制黑色描边
        pen = QPen(QColor(0, 0, 0, 200))
        pen.setWidth(3)
        painter.setPen(pen)
        painter.setFont(self.font())
        
        rect = self.rect()
        # 绘制多次形成描边效果
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    painter.drawText(rect.adjusted(dx, dy, dx, dy), Qt.AlignmentFlag.AlignLeft, self.text())
        
        # 绘制主文字
        color = self.palette().color(self.foregroundRole())
        painter.setPen(color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignLeft, self.text())


class LoginDialog(QWidget):
    """登录对话框"""
    
    login_success = pyqtSignal(Credential)
    
    def __init__(self):
        super().__init__()
        self.setupUI()
        
    def setupUI(self):
        self.setWindowTitle("Bilibili 登录")
        self.setFixedSize(450, 350)
        
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
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(140)
        
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
            self.login_success.emit(credential)
            QMessageBox.information(self, "成功", "登录信息已保存")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"登录失败: {str(e)}")


class VideoDetailDialog(QDialog):
    """视频详情对话框"""
    
    def __init__(self, video_info: dict, credential: Optional[Credential] = None, parent=None):
        super().__init__(parent)
        self.video_info = video_info
        self.credential = credential
        self.setupUI()
        
    def setupUI(self):
        self.setWindowTitle("视频详情")
        self.setMinimumSize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        
        # 视频封面
        cover_label = ImageLoader()
        cover_label.setFixedSize(640, 360)
        cover_label.setStyleSheet("background-color: #000; border-radius: 4px;")
        pic_url = self.video_info.get('pic', '')
        if pic_url and pic_url.startswith('//'):
            pic_url = 'https:' + pic_url
        if pic_url:
            cover_label.load_url(pic_url)
        content_layout.addWidget(cover_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 标题
        title = QLabel(self.video_info.get('title', '无标题'))
        title.setObjectName("titleLabel")
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        content_layout.addWidget(title)
        
        # UP主信息
        owner = self.video_info.get('owner', {})
        author_info = QLabel(f"UP主: {owner.get('name', '未知')} (uid: {owner.get('mid', 'N/A')})")
        author_info.setObjectName("subtitleLabel")
        content_layout.addWidget(author_info)
        
        # 统计信息
        stat = self.video_info.get('stat', {})
        stats_text = f"""
        观看: {self.format_count(stat.get('view', 0))} | 
        点赞: {self.format_count(stat.get('like', 0))} | 
        投币: {self.format_count(stat.get('coin', 0))} | 
        收藏: {self.format_count(stat.get('favorite', 0))} | 
        弹幕: {self.format_count(stat.get('danmaku', 0))} | 
        评论: {self.format_count(stat.get('reply', 0))}
        """
        stats_label = QLabel(stats_text.strip())
        stats_label.setWordWrap(True)
        content_layout.addWidget(stats_label)
        
        # BVID和时长
        bvid = self.video_info.get('bvid', 'N/A')
        duration = self.video_info.get('duration', 0)
        info_label = QLabel(f"BVID: {bvid} | 时长: {self.format_duration(duration)}")
        content_layout.addWidget(info_label)
        
        # 简介
        desc_group = QGroupBox("视频简介")
        desc_layout = QVBoxLayout(desc_group)
        desc_text = QTextEdit()
        desc_text.setPlainText(self.video_info.get('desc', '无简介'))
        desc_text.setReadOnly(True)
        desc_text.setMaximumHeight(150)
        desc_layout.addWidget(desc_text)
        content_layout.addWidget(desc_group)
        
        # 按钮组
        button_layout = QHBoxLayout()
        
        # 播放视频按钮
        play_btn = QPushButton("▶ 播放视频（带弹幕）")
        play_btn.clicked.connect(self.play_video)
        play_btn.setStyleSheet("background-color: #f25d8e; color: white; font-weight: bold; padding: 8px;")
        button_layout.addWidget(play_btn)
        
        # 在浏览器打开
        open_browser_btn = QPushButton("在浏览器中打开")
        open_browser_btn.clicked.connect(self.open_in_browser)
        button_layout.addWidget(open_browser_btn)
        
        # 复制链接
        copy_link_btn = QPushButton("复制链接")
        copy_link_btn.clicked.connect(self.copy_link)
        button_layout.addWidget(copy_link_btn)
        
        content_layout.addLayout(button_layout)
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
    def format_count(self, count: int) -> str:
        """格式化数字显示"""
        if count >= 10000:
            return f"{count/10000:.1f}万"
        return str(count)
        
    def format_duration(self, seconds: int) -> str:
        """格式化时长"""
        minutes = seconds // 60
        secs = seconds % 60
        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
    
    def play_video(self):
        """播放视频"""
        bvid = self.video_info.get('bvid', '')
        if bvid:
            # 打开视频播放器对话框
            player = VideoPlayerDialog(self.video_info, self.credential, self)
            player.exec()
        else:
            QMessageBox.warning(self, "提示", "无法获取视频信息")
        
    def open_in_browser(self):
        """在浏览器中打开"""
        bvid = self.video_info.get('bvid', '')
        if bvid:
            url = f"https://www.bilibili.com/video/{bvid}"
            QDesktopServices.openUrl(QUrl(url))
            
    def copy_link(self):
        """复制链接"""
        bvid = self.video_info.get('bvid', '')
        if bvid:
            url = f"https://www.bilibili.com/video/{bvid}"
            QApplication.clipboard().setText(url)
            QMessageBox.information(self, "成功", "链接已复制到剪贴板")


class LiveRoomCard(QFrame):
    """直播间卡片组件"""
    
    clicked = pyqtSignal(dict)
    
    def __init__(self, room_info: dict):
        super().__init__()
        self.room_info = room_info
        self.setupUI()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def setupUI(self):
        self.setObjectName("videoCard")
        self.setFixedSize(300, 280)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # 封面
        self.cover = ImageLoader(self)
        self.cover.setFixedSize(276, 155)
        self.cover.setStyleSheet("background-color: #e0e0e0; border-radius: 4px;")
        
        cover_url = self.room_info.get('cover', '') or self.room_info.get('user_cover', '')
        if cover_url:
            if cover_url.startswith('//'):
                cover_url = 'https:' + cover_url
            self.cover.load_url(cover_url)
        
        # 直播间标题
        title = self.room_info.get('title', '无标题')
        title_label = QLabel(title)
        title_label.setObjectName("titleLabel")
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(45)
        title_label.setStyleSheet("font-size: 14px; font-weight: 500;")
        
        # 主播信息
        uname = self.room_info.get('uname', '未知')
        author_label = QLabel(f"主播: {uname}")
        author_label.setObjectName("subtitleLabel")
        
        # 在线人数
        online = self.room_info.get('online', 0)
        stats_label = QLabel(f"👥 在线: {self.format_count(online)}")
        stats_label.setObjectName("subtitleLabel")
        
        layout.addWidget(self.cover)
        layout.addWidget(title_label)
        layout.addWidget(author_label)
        layout.addWidget(stats_label)
        layout.addStretch()
        
    def format_count(self, count: int) -> str:
        """格式化数字显示"""
        if count >= 10000:
            return f"{count/10000:.1f}万"
        return str(count)
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.room_info)
        super().mousePressEvent(event)


class DynamicCard(QFrame):
    """动态卡片组件"""
    
    clicked = pyqtSignal(dict)
    
    def __init__(self, dynamic_info: dict):
        super().__init__()
        self.dynamic_info = dynamic_info
        self.setupUI()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
    def setupUI(self):
        self.setObjectName("videoCard")
        self.setFixedSize(300, 280)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # 动态类型
        dtype = self.dynamic_info.get('type', '未知')
        type_label = QLabel(f"类型: {dtype}")
        type_label.setObjectName("subtitleLabel")
        type_label.setStyleSheet("color: #2196f3; font-weight: 500;")
        
        # 动态内容预览
        modules = self.dynamic_info.get('modules', {})
        desc = modules.get('module_dynamic', {}).get('desc', {})
        text = desc.get('text', '无内容')
        
        content_label = QLabel(text[:100] + ('...' if len(text) > 100 else ''))
        content_label.setObjectName("titleLabel")
        content_label.setWordWrap(True)
        content_label.setMaximumHeight(80)
        content_label.setStyleSheet("font-size: 13px;")
        
        # 作者信息
        author_info = modules.get('module_author', {})
        author_name = author_info.get('name', '未知')
        author_label = QLabel(f"作者: {author_name}")
        author_label.setObjectName("subtitleLabel")
        
        # 统计信息
        stat = modules.get('module_stat', {})
        like = stat.get('like', {}).get('count', 0)
        reply = stat.get('reply', {}).get('count', 0)
        
        stats_label = QLabel(f"👍 {like} | 💬 {reply}")
        stats_label.setObjectName("subtitleLabel")
        
        layout.addWidget(type_label)
        layout.addWidget(content_label)
        layout.addWidget(author_label)
        layout.addWidget(stats_label)
        layout.addStretch()
        
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.dynamic_info)
        super().mousePressEvent(event)


class UserProfileDialog(QDialog):
    """用户信息对话框"""
    
    def __init__(self, uid: int, credential: Optional[Credential] = None, parent=None):
        super().__init__(parent)
        self.uid = uid
        self.credential = credential
        self.setupUI()
        self.loadUserInfo()
        
    def setupUI(self):
        self.setWindowTitle("用户信息")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # 用户信息区域
        self.info_group = QGroupBox("用户信息")
        info_layout = QVBoxLayout(self.info_group)
        
        self.loading_label = QLabel("正在加载用户信息...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(self.loading_label)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        info_layout.addWidget(self.progress)
        
        layout.addWidget(self.info_group)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
    def loadUserInfo(self):
        """加载用户信息"""
        worker = UserInfoWorker(self.uid, self.credential)
        worker.finished.connect(self.onUserInfoLoaded)
        worker.error.connect(self.onUserInfoError)
        worker.start()
        
        self.user_worker = worker
        
    def onUserInfoLoaded(self, user_info: dict):
        """用户信息加载完成"""
        self.progress.setVisible(False)
        self.loading_label.setVisible(False)
        
        # 清空布局
        info_layout = self.info_group.layout()
        
        # 用户头像
        face_url = user_info.get('face', '')
        if face_url:
            avatar = ImageLoader()
            avatar.setFixedSize(100, 100)
            avatar.setStyleSheet("border-radius: 50px;")
            if face_url.startswith('//'):
                face_url = 'https:' + face_url
            avatar.load_url(face_url)
            info_layout.addWidget(avatar, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 用户名
        name = QLabel(user_info.get('name', '未知'))
        name.setObjectName("titleLabel")
        name.setStyleSheet("font-size: 20px; font-weight: bold;")
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(name)
        
        # UID
        uid_label = QLabel(f"UID: {user_info.get('mid', 'N/A')}")
        uid_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(uid_label)
        
        # 签名
        sign = user_info.get('sign', '这个人很懒，什么都没有留下')
        sign_label = QLabel(f"签名: {sign}")
        sign_label.setWordWrap(True)
        info_layout.addWidget(sign_label)
        
        # 统计信息
        stats_text = f"""
        等级: Lv{user_info.get('level', 0)}
        粉丝: {self.format_count(user_info.get('follower', 0))}
        关注: {self.format_count(user_info.get('following', 0))}
        """
        stats_label = QLabel(stats_text.strip())
        info_layout.addWidget(stats_label)
        
        # 在浏览器中打开
        open_btn = QPushButton("在浏览器中打开主页")
        open_btn.clicked.connect(lambda: self.openUserPage(user_info.get('mid')))
        info_layout.addWidget(open_btn)
        
    def onUserInfoError(self, error_msg: str):
        """用户信息加载失败"""
        self.progress.setVisible(False)
        self.loading_label.setText(f"加载失败: {error_msg}")
        
    def format_count(self, count: int) -> str:
        """格式化数字显示"""
        if count >= 10000:
            return f"{count/10000:.1f}万"
        return str(count)
        
    def openUserPage(self, uid):
        """在浏览器中打开用户主页"""
        if uid:
            url = f"https://space.bilibili.com/{uid}"
            QDesktopServices.openUrl(QUrl(url))


class UserInfoWorker(QThread):
    """用户信息工作线程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, uid: int, credential: Optional[Credential] = None):
        super().__init__()
        self.uid = uid
        self.credential = credential
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.fetch_user_info())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
            
    async def fetch_user_info(self):
        """获取用户信息"""
        try:
            u = user.User(uid=self.uid, credential=self.credential)
            info = await u.get_user_info()
            return info
        except Exception as e:
            raise e


class VideoPlayerDialog(QDialog):
    """视频播放器对话框（带弹幕）"""
    
    def __init__(self, video_info: dict, credential: Optional[Credential] = None, parent=None):
        super().__init__(parent)
        self.video_info = video_info
        self.credential = credential
        self.bvid = video_info.get('bvid', '')
        self.cid = 0
        self.danmakus = []
        self.danmaku_labels = []
        self.current_time = 0
        self.is_playing = False
        
        self.setupUI()
        self.loadVideoInfo()
        
    def setupUI(self):
        """设置UI"""
        self.setWindowTitle(f"播放: {self.video_info.get('title', '视频')}")
        self.setMinimumSize(960, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 视频播放容器
        video_container = QWidget()
        video_container.setStyleSheet("background-color: #000;")
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        
        # 视频播放器
        self.video_widget = QVideoWidget()
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        
        # 弹幕容器（覆盖在视频上方）
        self.danmaku_container = QWidget(self.video_widget)
        self.danmaku_container.setStyleSheet("background-color: transparent;")
        self.danmaku_container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        
        video_layout.addWidget(self.video_widget)
        
        # 控制栏
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(10, 5, 10, 5)
        
        # 播放/暂停按钮
        self.play_button = QPushButton("播放")
        self.play_button.setMaximumWidth(80)
        self.play_button.clicked.connect(self.togglePlayPause)
        controls_layout.addWidget(self.play_button)
        
        # 进度条
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(self.seek)
        controls_layout.addWidget(self.progress_slider)
        
        # 时间标签
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(100)
        controls_layout.addWidget(self.time_label)
        
        # 音量控制
        volume_label = QLabel("音量:")
        controls_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.valueChanged.connect(self.setVolume)
        controls_layout.addWidget(self.volume_slider)
        
        # 弹幕开关
        self.danmaku_checkbox = QPushButton("弹幕:开")
        self.danmaku_checkbox.setCheckable(True)
        self.danmaku_checkbox.setChecked(True)
        self.danmaku_checkbox.setMaximumWidth(80)
        self.danmaku_checkbox.clicked.connect(self.toggleDanmaku)
        controls_layout.addWidget(self.danmaku_checkbox)
        
        video_layout.addLayout(controls_layout)
        
        # 信息区域
        info_layout = QHBoxLayout()
        
        # 状态标签
        self.status_label = QLabel("正在加载视频...")
        info_layout.addWidget(self.status_label)
        
        info_layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setMaximumWidth(80)
        close_btn.clicked.connect(self.close)
        info_layout.addWidget(close_btn)
        
        layout.addWidget(video_container)
        layout.addLayout(info_layout)
        
        # 连接媒体播放器信号
        self.media_player.positionChanged.connect(self.updatePosition)
        self.media_player.durationChanged.connect(self.updateDuration)
        self.media_player.playbackStateChanged.connect(self.onPlaybackStateChanged)
        
        # 弹幕定时器
        self.danmaku_timer = QTimer()
        self.danmaku_timer.timeout.connect(self.updateDanmaku)
        self.danmaku_timer.start(100)  # 每100ms更新一次弹幕
        
    def loadVideoInfo(self):
        """加载视频信息"""
        # 首先获取CID
        worker = VideoInfoWorker(self.bvid, self.credential)
        worker.finished.connect(self.onVideoInfoLoaded)
        worker.error.connect(self.onVideoInfoError)
        worker.start()
        
        self.video_info_worker = worker
        
    def onVideoInfoLoaded(self, info: dict):
        """视频信息加载完成"""
        # 获取第一个分P的CID
        pages = info.get('pages', [])
        if pages:
            self.cid = pages[0].get('cid', 0)
            
            # 加载播放地址
            self.loadPlayUrl()
            
            # 加载弹幕
            self.loadDanmakus()
        else:
            self.status_label.setText("无法获取视频信息")
            
    def onVideoInfoError(self, error: str):
        """视频信息加载失败"""
        self.status_label.setText(f"加载失败: {error}")
        QMessageBox.critical(self, "错误", f"加载视频信息失败: {error}")
        
    def loadPlayUrl(self):
        """加载播放地址"""
        self.status_label.setText("正在获取播放地址...")
        
        worker = VideoPlayUrlWorker(self.bvid, self.cid, self.credential)
        worker.finished.connect(self.onPlayUrlLoaded)
        worker.error.connect(self.onPlayUrlError)
        worker.start()
        
        self.play_url_worker = worker
        
    def onPlayUrlLoaded(self, play_info: dict):
        """播放地址加载完成"""
        try:
            # 尝试获取播放URL
            durl = play_info.get('durl', [])
            if durl:
                url = durl[0].get('url', '')
                if url:
                    self.media_player.setSource(QUrl(url))
                    self.status_label.setText("准备就绪，点击播放")
                    return
            
            # 尝试dash格式
            dash = play_info.get('dash', {})
            video_list = dash.get('video', [])
            if video_list:
                url = video_list[0].get('baseUrl', '') or video_list[0].get('base_url', '')
                if url:
                    self.media_player.setSource(QUrl(url))
                    self.status_label.setText("准备就绪，点击播放")
                    return
            
            self.status_label.setText("无法获取播放地址")
            QMessageBox.warning(self, "提示", "该视频可能需要大会员权限或其他原因无法播放。建议在浏览器中打开。")
        except Exception as e:
            self.status_label.setText(f"解析播放地址失败: {str(e)}")
            
    def onPlayUrlError(self, error: str):
        """播放地址加载失败"""
        self.status_label.setText(f"获取播放地址失败: {error}")
        QMessageBox.critical(self, "错误", f"获取播放地址失败: {error}\n\n建议在浏览器中打开观看。")
        
    def loadDanmakus(self):
        """加载弹幕"""
        worker = DanmakuWorker(self.bvid, self.cid, self.credential)
        worker.finished.connect(self.onDanmakusLoaded)
        worker.error.connect(lambda e: print(f"加载弹幕失败: {e}"))
        worker.start()
        
        self.danmaku_worker = worker
        
    def onDanmakusLoaded(self, danmakus: list):
        """弹幕加载完成"""
        self.danmakus = danmakus
        print(f"已加载 {len(danmakus)} 条弹幕")
        
    def togglePlayPause(self):
        """切换播放/暂停"""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
            
    def onPlaybackStateChanged(self, state):
        """播放状态改变"""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("暂停")
            self.is_playing = True
        else:
            self.play_button.setText("播放")
            self.is_playing = False
            
    def updatePosition(self, position):
        """更新播放位置"""
        self.current_time = position / 1000.0  # 转换为秒
        
        # 更新进度条
        if self.media_player.duration() > 0:
            self.progress_slider.setValue(int(position / self.media_player.duration() * 1000))
        
        # 更新时间显示
        current = self.formatTime(position // 1000)
        total = self.formatTime(self.media_player.duration() // 1000)
        self.time_label.setText(f"{current} / {total}")
        
    def updateDuration(self, duration):
        """更新总时长"""
        pass
        
    def seek(self, position):
        """跳转到指定位置"""
        if self.media_player.duration() > 0:
            target = int(position / 1000 * self.media_player.duration())
            self.media_player.setPosition(target)
            
    def setVolume(self, value):
        """设置音量"""
        self.audio_output.setVolume(value / 100.0)
        
    def toggleDanmaku(self):
        """切换弹幕显示"""
        if self.danmaku_checkbox.isChecked():
            self.danmaku_checkbox.setText("弹幕:开")
        else:
            self.danmaku_checkbox.setText("弹幕:关")
            # 清除当前弹幕
            for label in self.danmaku_labels:
                label.deleteLater()
            self.danmaku_labels.clear()
            
    def updateDanmaku(self):
        """更新弹幕显示"""
        if not self.is_playing or not self.danmaku_checkbox.isChecked():
            return
            
        # 查找当前时间应该显示的弹幕
        for danmaku in self.danmakus:
            dm_time = danmaku.dm_time
            # 允许50ms的误差
            if abs(dm_time - self.current_time) < 0.5:
                # 创建弹幕标签
                self.createDanmakuLabel(danmaku)
        
        # 清理已经移出屏幕的弹幕
        for label in self.danmaku_labels[:]:
            if label.x() + label.width() < 0:
                label.deleteLater()
                self.danmaku_labels.remove(label)
                
    def createDanmakuLabel(self, danmaku: Danmaku):
        """创建弹幕标签"""
        # 弹幕颜色
        color = QColor(danmaku.color) if hasattr(danmaku, 'color') else QColor(255, 255, 255)
        
        # 创建标签
        label = DanmakuLabel(danmaku.text, color, self.danmaku_container)
        label.adjustSize()
        
        # 随机Y位置
        container_height = self.danmaku_container.height()
        if container_height > 0:
            y = random.randint(0, max(0, container_height - label.height() - 50))
        else:
            y = random.randint(0, 400)
        
        # 初始位置在右边屏幕外
        x = self.danmaku_container.width()
        label.move(x, y)
        label.show()
        
        self.danmaku_labels.append(label)
        
        # 创建动画
        animation = QPropertyAnimation(label, b"pos")
        animation.setDuration(8000)  # 8秒划过屏幕
        animation.setStartValue(QPoint(x, y))
        animation.setEndValue(QPoint(-label.width(), y))
        animation.setEasingCurve(QEasingCurve.Type.Linear)
        animation.start()
        
        # 保存动画引用避免被垃圾回收
        label.animation = animation
        
    def resizeEvent(self, event):
        """窗口大小改变"""
        super().resizeEvent(event)
        # 调整弹幕容器大小
        if hasattr(self, 'danmaku_container'):
            self.danmaku_container.resize(self.video_widget.size())
            
    def formatTime(self, seconds):
        """格式化时间"""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"
        
    def closeEvent(self, event):
        """关闭事件"""
        self.media_player.stop()
        self.danmaku_timer.stop()
        super().closeEvent(event)


class VideoInfoWorker(QThread):
    """视频信息工作线程（用于获取CID）"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, bvid: str, credential: Optional[Credential] = None):
        super().__init__()
        self.bvid = bvid
        self.credential = credential
        
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.fetch_info())
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
            
    async def fetch_info(self):
        """获取视频信息"""
        try:
            v = video.Video(bvid=self.bvid, credential=self.credential)
            info = await v.get_info()
            return info
        except Exception as e:
            raise e


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
            ("📝 动态", self.showDynamic),
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
        
        # 推荐视频选项卡
        self.recommend_tab = self.createVideoGridTab("推荐")
        self.tab_widget.addTab(self.recommend_tab, "🏠 推荐")
        
        # 热门视频选项卡
        self.hot_tab = self.createVideoGridTab("热门")
        self.tab_widget.addTab(self.hot_tab, "🔥 热门")
        
        # 搜索结果选项卡
        self.search_tab = self.createVideoGridTab("搜索结果")
        self.tab_widget.addTab(self.search_tab, "🔍 搜索")
        
        # 直播选项卡
        self.live_tab = self.createVideoGridTab("直播")
        self.tab_widget.addTab(self.live_tab, "📺 直播")
        
        # 动态选项卡
        self.dynamic_tab = self.createVideoGridTab("动态")
        self.tab_widget.addTab(self.dynamic_tab, "📝 动态")
        
        layout.addWidget(self.tab_widget)
        
        # 自动加载推荐内容
        QTimer.singleShot(500, self.loadRecommendVideos)
        
        return main_content
        
    def createVideoGridTab(self, tab_name: str):
        """创建视频网格布局选项卡"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 标题和进度条容器
        header_layout = QHBoxLayout()
        
        # 标题
        title = QLabel(tab_name)
        title.setObjectName("titleLabel")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("刷新")
        refresh_btn.setMaximumWidth(80)
        refresh_btn.clicked.connect(lambda: self.refreshTab(tab_name))
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # 进度条
        progress_bar = QProgressBar()
        progress_bar.setVisible(False)
        progress_bar.setObjectName(f"{tab_name}_progress")
        layout.addWidget(progress_bar)
        
        # 滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content_widget = QWidget()
        grid_layout = QGridLayout(content_widget)
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        grid_layout.setObjectName(f"{tab_name}_grid")
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        # 保存引用
        setattr(self, f"{tab_name}_title", title)
        setattr(self, f"{tab_name}_progress", progress_bar)
        setattr(self, f"{tab_name}_grid", grid_layout)
        setattr(self, f"{tab_name}_content", content_widget)
        
        return tab
        
    def setupStyle(self):
        """应用Material Design样式"""
        self.setStyleSheet(MATERIAL_THEME)
    
    def clearGrid(self, grid_layout):
        """清空网格布局"""
        for i in reversed(range(grid_layout.count())):
            item = grid_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
    
    def displayVideosInGrid(self, videos: list, grid_layout, is_live=False):
        """在网格中显示视频"""
        row, col = 0, 0
        max_cols = 3  # 每行最多3个卡片
        
        for video_info in videos:
            try:
                if is_live:
                    card = LiveRoomCard(video_info)
                    card.clicked.connect(self.onLiveRoomClicked)
                else:
                    if 'bvid' in video_info or 'id' in video_info or 'aid' in video_info:
                        card = VideoCard(video_info)
                        card.clicked.connect(self.onVideoCardClicked)
                    else:
                        continue
                
                grid_layout.addWidget(card, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            except Exception as e:
                print(f"创建卡片失败: {e}")
                continue
    
    def search(self):
        """执行搜索"""
        keyword = self.search_edit.text().strip()
        if not keyword:
            return
            
        # 显示进度条
        progress = getattr(self, "搜索结果_progress")
        progress.setVisible(True)
        progress.setRange(0, 0)
        self.statusBar().showMessage(f"正在搜索: {keyword}")
        
        # 清空之前的搜索结果
        grid = getattr(self, "搜索结果_grid")
        self.clearGrid(grid)
        
        # 创建搜索工作线程
        self.search_worker = SearchWorker(keyword)
        self.search_worker.search_finished.connect(lambda results: self.onSearchFinished(results, keyword))
        self.search_worker.search_error.connect(self.onSearchError)
        self.search_worker.start()
        
    def onSearchFinished(self, results: list, keyword: str):
        """搜索完成回调"""
        progress = getattr(self, "搜索结果_progress")
        progress.setVisible(False)
        self.statusBar().showMessage(f"搜索完成，找到 {len(results)} 个结果")
        
        # 更新标题
        title = getattr(self, "搜索结果_title")
        title.setText(f"搜索结果: {keyword} ({len(results)})")
        
        # 显示搜索结果
        grid = getattr(self, "搜索结果_grid")
        self.displayVideosInGrid(results, grid)
        
        # 切换到搜索结果选项卡
        self.tab_widget.setCurrentWidget(self.search_tab)
        
    def onSearchError(self, error_msg: str):
        """搜索错误回调"""
        progress = getattr(self, "搜索结果_progress")
        progress.setVisible(False)
        self.statusBar().showMessage("搜索失败")
        QMessageBox.critical(self, "搜索错误", f"搜索失败: {error_msg}")
    
    def loadRecommendVideos(self):
        """加载推荐视频"""
        progress = getattr(self, "推荐_progress")
        progress.setVisible(True)
        progress.setRange(0, 0)
        self.statusBar().showMessage("正在加载推荐视频...")
        
        worker = RecommendVideosWorker()
        worker.finished.connect(self.onRecommendVideosLoaded)
        worker.error.connect(lambda e: self.onContentLoadError("推荐", e))
        worker.start()
        
        # 保存worker引用避免被垃圾回收
        self.recommend_worker = worker
        
    def onRecommendVideosLoaded(self, videos: list):
        """推荐视频加载完成"""
        progress = getattr(self, "推荐_progress")
        progress.setVisible(False)
        self.statusBar().showMessage(f"推荐视频加载完成，共 {len(videos)} 个")
        
        title = getattr(self, "推荐_title")
        title.setText(f"推荐 ({len(videos)})")
        
        grid = getattr(self, "推荐_grid")
        self.clearGrid(grid)
        self.displayVideosInGrid(videos, grid)
        
    def loadHotVideos(self):
        """加载热门视频"""
        progress = getattr(self, "热门_progress")
        progress.setVisible(True)
        progress.setRange(0, 0)
        self.statusBar().showMessage("正在加载热门视频...")
        
        worker = HotVideosWorker()
        worker.finished.connect(self.onHotVideosLoaded)
        worker.error.connect(lambda e: self.onContentLoadError("热门", e))
        worker.start()
        
        self.hot_worker = worker
        
    def onHotVideosLoaded(self, videos: list):
        """热门视频加载完成"""
        progress = getattr(self, "热门_progress")
        progress.setVisible(False)
        self.statusBar().showMessage(f"热门视频加载完成，共 {len(videos)} 个")
        
        title = getattr(self, "热门_title")
        title.setText(f"热门 ({len(videos)})")
        
        grid = getattr(self, "热门_grid")
        self.clearGrid(grid)
        self.displayVideosInGrid(videos, grid)
        
    def loadLiveRooms(self):
        """加载直播间"""
        progress = getattr(self, "直播_progress")
        progress.setVisible(True)
        progress.setRange(0, 0)
        self.statusBar().showMessage("正在加载直播间...")
        
        worker = LiveRoomsWorker()
        worker.finished.connect(self.onLiveRoomsLoaded)
        worker.error.connect(lambda e: self.onContentLoadError("直播", e))
        worker.start()
        
        self.live_worker = worker
        
    def onLiveRoomsLoaded(self, rooms: list):
        """直播间加载完成"""
        progress = getattr(self, "直播_progress")
        progress.setVisible(False)
        self.statusBar().showMessage(f"直播间加载完成，共 {len(rooms)} 个")
        
        title = getattr(self, "直播_title")
        title.setText(f"直播 ({len(rooms)})")
        
        grid = getattr(self, "直播_grid")
        self.clearGrid(grid)
        self.displayVideosInGrid(rooms, grid, is_live=True)
    
    def loadDynamics(self):
        """加载动态"""
        if not self.credential:
            QMessageBox.information(self, "提示", "请先登录以查看动态")
            return
            
        progress = getattr(self, "动态_progress")
        progress.setVisible(True)
        progress.setRange(0, 0)
        self.statusBar().showMessage("正在加载动态...")
        
        # 获取当前登录用户的UID（这里使用一个示例UID，实际应该从登录信息获取）
        # 由于无法直接从credential获取uid，我们加载全站动态
        worker = AllDynamicsWorker()
        worker.finished.connect(self.onDynamicsLoaded)
        worker.error.connect(lambda e: self.onContentLoadError("动态", e))
        worker.start()
        
        self.dynamics_worker = worker
        
    def onDynamicsLoaded(self, dynamics: list):
        """动态加载完成"""
        progress = getattr(self, "动态_progress")
        progress.setVisible(False)
        self.statusBar().showMessage(f"动态加载完成，共 {len(dynamics)} 条")
        
        title = getattr(self, "动态_title")
        title.setText(f"动态 ({len(dynamics)})")
        
        grid = getattr(self, "动态_grid")
        self.clearGrid(grid)
        
        # 显示动态卡片
        row, col = 0, 0
        max_cols = 3
        
        for dynamic_info in dynamics:
            try:
                card = DynamicCard(dynamic_info)
                card.clicked.connect(self.onDynamicClicked)
                grid.addWidget(card, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
            except Exception as e:
                print(f"创建动态卡片失败: {e}")
                continue
        
    def onDynamicClicked(self, dynamic_info: dict):
        """动态卡片点击事件"""
        # 获取动态ID并在浏览器中打开
        dynamic_id = dynamic_info.get('id_str', '')
        if dynamic_id:
            url = f"https://t.bilibili.com/{dynamic_id}"
            QDesktopServices.openUrl(QUrl(url))
        else:
            QMessageBox.information(self, "提示", "无法获取动态信息")
        
    def onContentLoadError(self, content_type: str, error_msg: str):
        """内容加载错误"""
        progress = getattr(self, f"{content_type}_progress")
        progress.setVisible(False)
        self.statusBar().showMessage(f"{content_type}加载失败")
        QMessageBox.warning(self, "加载错误", f"{content_type}加载失败: {error_msg}")
        
    def refreshTab(self, tab_name: str):
        """刷新选项卡内容"""
        if tab_name == "推荐":
            self.loadRecommendVideos()
        elif tab_name == "热门":
            self.loadHotVideos()
        elif tab_name == "直播":
            self.loadLiveRooms()
        elif tab_name == "动态":
            self.loadDynamics()
        elif tab_name == "搜索结果":
            self.search()
            
    def onVideoCardClicked(self, video_info: dict):
        """视频卡片点击事件"""
        bvid = video_info.get('bvid', '') or video_info.get('id', '')
        if not bvid:
            # 尝试从aid获取bvid
            aid = video_info.get('aid', 0)
            if aid:
                try:
                    bvid = bilibili_api.bvid2aid(aid)
                except:
                    pass
        
        if bvid:
            # 显示视频详情对话框，传递凭据
            dialog = VideoDetailDialog(video_info, self.credential, self)
            dialog.exec()
        else:
            QMessageBox.information(self, "提示", "无法获取视频信息")
            
    def onLiveRoomClicked(self, room_info: dict):
        """直播间卡片点击事件"""
        room_id = room_info.get('roomid', '') or room_info.get('room_id', '')
        if room_id:
            url = f"https://live.bilibili.com/{room_id}"
            QDesktopServices.openUrl(QUrl(url))
        else:
            QMessageBox.information(self, "提示", "无法获取直播间信息")
        
    def showLoginDialog(self):
        """显示登录对话框"""
        dialog = LoginDialog()
        dialog.login_success.connect(self.onLoginSuccess)
        dialog.show()
        
        # 保存引用避免被垃圾回收
        self.login_dialog = dialog
        
    def onLoginSuccess(self, credential: Credential):
        """登录成功回调"""
        self.credential = credential
        self.user_name.setText("已登录")
        self.statusBar().showMessage("登录成功")
        
    def logout(self):
        """登出"""
        self.credential = None
        self.user_name.setText("点击登录")
        self.user_avatar.setText("未登录")
        self.statusBar().showMessage("已登出")
        
    def refresh(self):
        """刷新当前选项卡内容"""
        current_tab = self.tab_widget.currentWidget()
        if current_tab == self.recommend_tab:
            self.loadRecommendVideos()
        elif current_tab == self.hot_tab:
            self.loadHotVideos()
        elif current_tab == self.live_tab:
            self.loadLiveRooms()
        elif current_tab == self.search_tab:
            if hasattr(self, 'search_worker') and self.search_worker:
                self.search()
        
    def showAbout(self):
        """显示关于信息"""
        QMessageBox.about(
            self, 
            "关于", 
            f"Bilibili 第三方客户端\n\n"
            f"基于 bilibili-api {bilibili_api.BILIBILI_API_VERSION}\n"
            f"使用 PyQt6 和 Material Design\n\n"
            f"功能特性：\n"
            f"• 视频搜索和浏览\n"
            f"• 推荐视频展示\n"
            f"• 热门视频展示\n"
            f"• 直播间浏览\n"
            f"• 视频详情查看\n\n"
            f"仅供学习和测试使用"
        )
        
    # 导航按钮回调函数
    def showHome(self):
        """显示首页"""
        self.tab_widget.setCurrentWidget(self.recommend_tab)
        if not hasattr(self, 'recommend_worker') or not self.recommend_worker:
            self.loadRecommendVideos()
        
    def showHot(self):
        """显示热门"""
        self.tab_widget.setCurrentWidget(self.hot_tab)
        if not hasattr(self, 'hot_worker') or not self.hot_worker:
            self.loadHotVideos()
        
    def showLive(self):
        """显示直播"""
        self.tab_widget.setCurrentWidget(self.live_tab)
        if not hasattr(self, 'live_worker') or not self.live_worker:
            self.loadLiveRooms()
    
    def showDynamic(self):
        """显示动态"""
        self.tab_widget.setCurrentWidget(self.dynamic_tab)
        if not hasattr(self, 'dynamics_worker') or not self.dynamics_worker:
            self.loadDynamics()
        
    def showMusic(self):
        """显示音乐"""
        self.statusBar().showMessage("音乐功能即将推出...")
        
    def showArticle(self):
        """显示专栏"""
        self.statusBar().showMessage("专栏功能即将推出...")
        
    def showGame(self):
        """显示游戏"""
        self.statusBar().showMessage("游戏功能即将推出...")
        

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