#!/usr/bin/env python3
"""
Bilibili 第三方客户端启动入口
"""

def main():
    from bilibili_api.tools.client.main_window import main as app_main
    app_main()

if __name__ == "__main__":
    main()