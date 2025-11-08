# Bilibili 第三方客户端

基于 `bilibili-api` 和 PyQt6 开发的完整功能 Bilibili 第三方客户端，采用 Material Design 风格设计。

## 功能特点

- 🎨 **Material Design** - 采用现代化的 Material Design 设计风格
- 🔍 **视频搜索** - 支持搜索 Bilibili 视频内容，实时显示搜索结果
- 🏠 **推荐视频** - 自动加载 Bilibili 推荐视频流
- 🔥 **热门视频** - 展示 Bilibili 热门视频排行
- 📺 **直播浏览** - 浏览热门直播间，一键打开直播
- 🖼️ **视频封面** - 自动加载视频和直播间封面图片
- 📝 **视频详情** - 查看完整的视频信息、统计数据和简介
- 👤 **用户登录** - 支持用户登录功能（需要手动配置凭据）
- 🌐 **浏览器打开** - 支持在浏览器中打开视频和直播间
- 📋 **链接复制** - 一键复制视频链接到剪贴板
- 📱 **响应式布局** - 自适应窗口大小的界面设计
- 🔧 **模块化设计** - 清晰的代码结构，易于扩展

## 界面预览

客户端包含以下主要界面：

- **主界面**: 包含搜索栏、导航侧边栏、多标签页内容区域
- **推荐页**: 展示个性化推荐视频，带封面和统计信息
- **热门页**: 展示当前热门视频排行榜
- **搜索页**: 以卡片形式展示视频搜索结果
- **直播页**: 浏览热门直播间，显示在线人数
- **视频详情**: 完整的视频信息对话框，包含封面、简介、统计数据
- **登录界面**: 用户凭据输入界面
- **用户信息**: 侧边栏显示用户头像和基本信息

## 安装和运行

### 系统要求

- Python 3.9+
- PyQt6
- bilibili-api 及其依赖

### 运行方式

1. **直接运行模块**:
   ```bash
   python -m bilibili_api.tools.client
   ```

2. **安装后使用命令**:
   ```bash
   pip install -e .
   bilibili-client
   ```

### 依赖安装

如果遇到依赖问题，请安装以下包：

```bash
pip install PyQt6 aiohttp yarl pillow beautifulsoup4 lxml pyyaml brotli qrcode APScheduler pycryptodomex qrcode-terminal PyJWT
```

## 使用说明

### 搜索视频

1. 在顶部搜索栏输入关键词
2. 点击搜索按钮或按回车键
3. 搜索结果将以卡片形式显示，包含视频封面、标题、UP主信息和统计数据
4. 点击视频卡片查看详细信息

### 浏览内容

- **推荐页**: 启动客户端后自动加载推荐视频
- **热门页**: 点击侧边栏"🔥 热门"按钮或导航到热门标签页
- **直播页**: 点击侧边栏"📺 直播"按钮浏览热门直播间
- **刷新**: 每个标签页都有刷新按钮，可重新加载内容

### 查看视频详情

1. 点击任意视频卡片
2. 弹出详情对话框，显示：
   - 高清视频封面
   - 完整标题和 UP主信息
   - 详细统计数据（观看、点赞、投币、收藏、弹幕、评论）
   - 视频简介
   - BVID 和时长信息
3. 可以在浏览器中打开或复制视频链接

### 观看直播

1. 导航到"📺 直播"标签页
2. 浏览热门直播间列表
3. 点击直播间卡片
4. 自动在浏览器中打开直播间

### 用户登录

1. 点击菜单栏中的"用户" -> "登录"
2. 按照对话框中的说明获取登录凭据
3. 输入 SESSDATA、bili_jct、buvid3
4. 点击登录按钮
5. 登录后可以使用需要认证的功能

### 界面导航

- **侧边栏**: 包含用户信息和导航菜单
- **搜索结果**: 点击视频卡片查看详情（功能待完善）
- **状态栏**: 显示应用程序当前状态

## 技术架构

### 主要组件

- `main_window.py` - 主窗口和应用程序逻辑（完整功能实现）
- `material_style.py` - Material Design 样式表
- `__init__.py` - 包初始化
- `__main__.py` - 程序入口点
- `demo.py` - UI 组件演示脚本

### 核心类

- **ImageLoader** - 异步图片加载器，用于加载视频封面和直播间封面
- **VideoCard** - 视频卡片组件，显示视频信息
- **LiveRoomCard** - 直播间卡片组件，显示直播间信息
- **VideoDetailDialog** - 视频详情对话框，展示完整视频信息
- **LoginDialog** - 登录对话框，处理用户凭据输入
- **SearchWorker** - 搜索工作线程，异步执行视频搜索
- **HotVideosWorker** - 热门视频工作线程，获取热门视频
- **RecommendVideosWorker** - 推荐视频工作线程，获取推荐内容
- **LiveRoomsWorker** - 直播间工作线程，获取直播间列表
- **BilibiliClient** - 主窗口类，管理整个应用程序

### 设计模式

- **MVC架构**: 界面与业务逻辑分离
- **工作线程**: 异步处理网络请求，避免界面卡顿
- **信号槽机制**: PyQt6 信号槽实现组件间通信
- **组件化设计**: 可复用的UI组件（视频卡片、直播卡片等）
- **网格布局**: 统一的内容展示方式，支持多列布局

### Material Design 特性

- 卡片式布局，带阴影和圆角
- 扁平化按钮设计，支持悬停效果
- 现代色彩搭配（蓝色主题）
- 响应式交互效果（悬停、点击状态）
- 清晰的排版层次
- 无限进度条，优雅的加载提示
- 统一的图标和emoji使用

## 已实现功能

✅ 视频搜索与展示  
✅ 推荐视频流  
✅ 热门视频排行  
✅ 直播间浏览  
✅ 视频详情查看  
✅ 视频封面加载  
✅ 在浏览器中打开  
✅ 链接复制  
✅ 用户登录  
✅ 多标签页导航  
✅ 刷新功能  
✅ 响应式布局  

## 开发与扩展

### 添加新功能

1. 在 `main_window.py` 中添加新的工作线程类（继承 QThread）
2. 实现异步数据获取方法
3. 创建对应的UI组件或复用现有组件
4. 在主窗口中添加新的标签页或功能入口
5. 在 `material_style.py` 中添加相应的样式

### 扩展示例

```python
# 添加新的工作线程
class MyCustomWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def run(self):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(self.fetch_data())
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()
    
    async def fetch_data(self):
        # 使用 bilibili_api 获取数据
        pass
```

### 自定义样式

修改 `material_style.py` 中的 CSS 样式来自定义界面外观：

```python
MATERIAL_THEME = """
/* 修改主题颜色 */
QToolBar {
    background-color: #your-color;
}
```

## 注意事项

- 本客户端仅供学习和测试使用
- 请遵守 Bilibili 服务条款和相关法规
- 用户凭据需要手动获取，请勿泄露给他人
- 部分功能仍在开发中

## 许可证

遵循 `bilibili-api` 项目的 GPL-3.0-or-later 许可证。