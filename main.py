#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序入口
"""

import sys

if __name__ == "__main__":
    """启动应用"""
    # 默认启动tkinter桌面应用
    import tkinter as tk
    from ui.desktop_app import DesktopApp
    
    root = tk.Tk()
    app = DesktopApp(root)
    root.mainloop()


