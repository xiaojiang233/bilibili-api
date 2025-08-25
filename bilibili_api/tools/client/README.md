# Bilibili 第三方客户端

基于 `bilibili-api` 和 PyQt6 开发的 Bilibili 第三方客户端，采用 Material Design 风格设计。

## 功能特点

- 🎨 **Material Design** - 采用现代化的 Material Design 设计风格
- 🔍 **视频搜索** - 支持搜索 Bilibili 视频内容
- 👤 **用户登录** - 支持用户登录功能（需要手动配置凭据）
- 📱 **响应式布局** - 自适应窗口大小的界面设计
- 🔧 **模块化设计** - 清晰的代码结构，易于扩展

## 界面预览

客户端包含以下主要界面：

- **主界面**: 包含搜索栏、导航侧边栏、内容显示区域
- **搜索结果**: 以卡片形式展示视频信息
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
3. 搜索结果将以卡片形式显示在主内容区域

### 用户登录

1. 点击菜单栏中的"用户" -> "登录"
2. 按照对话框中的说明获取登录凭据
3. 输入 SESSDATA、bili_jct、buvid3
4. 点击登录按钮

### 界面导航

- **侧边栏**: 包含用户信息和导航菜单
- **搜索结果**: 点击视频卡片查看详情（功能待完善）
- **状态栏**: 显示应用程序当前状态

## 技术架构

### 主要组件

- `main_window.py` - 主窗口和应用程序逻辑
- `material_style.py` - Material Design 样式表
- `__init__.py` - 包初始化
- `__main__.py` - 程序入口点

### 设计模式

- **MVC架构**: 界面与业务逻辑分离
- **工作线程**: 异步处理网络请求，避免界面卡顿
- **组件化设计**: 可复用的UI组件

### Material Design 特性

- 卡片式布局
- 扁平化按钮设计  
- 现代色彩搭配（蓝色主题）
- 响应式交互效果
- 清晰的排版层次

## 开发与扩展

### 添加新功能

1. 在 `main_window.py` 中添加新的界面组件
2. 创建对应的异步工作线程处理业务逻辑
3. 在 `material_style.py` 中添加相应的样式

### 自定义样式

修改 `material_style.py` 中的 CSS 样式来自定义界面外观。

## 注意事项

- 本客户端仅供学习和测试使用
- 请遵守 Bilibili 服务条款和相关法规
- 用户凭据需要手动获取，请勿泄露给他人
- 部分功能仍在开发中

## 许可证

遵循 `bilibili-api` 项目的 GPL-3.0-or-later 许可证。