"""
太阳系轨道设计工具 - 主程序入口
"""
import tkinter as tk
from ui.desktop_app import DesktopApp

if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopApp(root)
    root.mainloop()