import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DesktopApp:
    """桌面应用类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("太阳系轨道设计工具")
        self.root.geometry("1200x800")
        self.root.configure(bg="#2d2d2d")
        
        # 初始化所有属性（避免 AttributeError）
        self.fig = None
        self.canvas = None
        self.ax = None
        self.current_view = None
        self.solar_system = None
        self.current_date = datetime.now()
        
        # 第一步：创建所有 UI 控件（不依赖 core 模块）
        self._create_ui()
        
        # 第二步：设置窗口关闭时的资源清理回调
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 第三步：尝试加载核心模块
        self._init_core_module()
    
    def _create_ui(self):
        """创建所有界面控件（必须在任何可能失败的操作之前执行）"""
        # 设置暗色风格
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Dark.TFrame", background="#2d2d2d")
        style.configure("Dark.TLabelframe", background="#2d2d2d", foreground="white")
        style.configure("Dark.TLabelframe.Label", background="#2d2d2d", foreground="white")
        style.configure("Dark.TLabel", background="#2d2d2d", foreground="white")
        style.configure("Dark.TButton", background="#404040", foreground="white")
        style.configure("Dark.Horizontal.TScale", background="#2d2d2d", foreground="white")
        
        # 主框架
        self.main_frame = ttk.Frame(self.root, padding="10", style="Dark.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 控制面板
        self.control_frame = ttk.LabelFrame(self.main_frame, text="控制面板", padding="10", style="Dark.TLabelframe")
        self.control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 日期显示
        self.date_var = tk.StringVar(value=f"{self.current_date.year}-{self.current_date.month:02d}-{self.current_date.day:02d}")
        ttk.Label(self.control_frame, text="当前日期:", font=('Arial', 10, 'bold'), style="Dark.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Label(self.control_frame, textvariable=self.date_var, font=('Arial', 10), style="Dark.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        
        # 时间滑块
        ttk.Label(self.control_frame, text="时间调整:", font=('Arial', 10, 'bold'), style="Dark.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        self.time_slider = ttk.Scale(self.control_frame, from_=-365, to=365, orient=tk.HORIZONTAL, length=400, command=self.update_date, style="Dark.Horizontal.TScale")
        self.time_slider.set(0)
        self.time_slider.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 滑块值显示
        self.slider_value_var = tk.StringVar(value="0 天")
        ttk.Label(self.control_frame, textvariable=self.slider_value_var, font=('Arial', 10), style="Dark.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        
        # 可视化框架
        self.viz_frame = ttk.LabelFrame(self.main_frame, text="太阳系可视化", padding="10", style="Dark.TLabelframe")
        self.viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _init_core_module(self):
        """尝试导入并初始化 SolarSystem 模块"""
        try:
            from core.solar_system import SolarSystem
            self.solar_system = SolarSystem()
            # 初始化成功，进行首次绘图
            self.update_solar_system()
        except Exception as e:
            # 显示错误并禁用时间滑块，但窗口仍然可以正常关闭
            messagebox.showerror("初始化错误", 
                f"无法加载太阳系模块：{str(e)}\n\n程序将无法显示太阳系可视化，但窗口可以正常关闭。")
            self.time_slider.config(state=tk.DISABLED)
            # 在可视化框架中显示错误信息
            error_label = ttk.Label(self.viz_frame, text=f"核心模块加载失败:\n{str(e)}", 
                                    style="Dark.TLabel", font=('Arial', 12))
            error_label.pack(expand=True)
    
    def on_closing(self):
        """窗口关闭时清理 Matplotlib 资源并退出"""
        try:
            # 关闭所有 matplotlib 图形
            plt.close('all')
            # 销毁画布部件
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            # 销毁主窗口
            self.root.destroy()
        except Exception as e:
            print(f"清理资源时出错: {e}")
        finally:
            # 确保进程退出（解决某些环境下的残留问题）
            sys.exit(0)
    
    def update_date(self, value):
        """滑块回调：更新日期和可视化"""
        # 如果核心模块未就绪，不做任何操作
        if self.solar_system is None:
            return
        
        try:
            days = int(float(value))
            adjusted_date = self.current_date.replace(hour=0, minute=0, second=0, microsecond=0)
            adjusted_date = adjusted_date.fromordinal(adjusted_date.toordinal() + days)
            
            # 更新界面控件（它们一定存在，因为 UI 已先创建）
            self.date_var.set(f"{adjusted_date.year}-{adjusted_date.month:02d}-{adjusted_date.day:02d}")
            self.slider_value_var.set(f"{days} 天")
            
            # 更新可视化
            self.update_solar_system(adjusted_date)
        except Exception as e:
            print(f"更新日期时出现错误: {str(e)}")
    
    def update_solar_system(self, date=None):
        """更新太阳系可视化（含资源管理）"""
        if self.solar_system is None:
            return
        
        try:
            if date is None:
                date = self.current_date
            
            # 保存当前视角（如果 ax 存在）
            if self.ax is not None:
                self.current_view = {
                    'xlim': self.ax.get_xlim(),
                    'ylim': self.ax.get_ylim(),
                    'zlim': self.ax.get_zlim(),
                    'elev': self.ax.elev,
                    'azim': self.ax.azim
                }
            
            # 检查是否需要重新创建画布
            if self.fig is None or self.canvas is None or self.ax is None:
                # 关闭旧的 figure 避免资源泄漏
                if self.fig is not None:
                    plt.close(self.fig)
                
                self.fig = plt.figure(figsize=(20, 8), facecolor='black')
                self.ax = self.fig.add_subplot(111, projection='3d')
                self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
                self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
                self.canvas = FigureCanvasTkAgg(self.fig, master=self.viz_frame)
                self.canvas.draw()
                self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            else:
                self.ax.clear()
            
            # 调用核心绘图函数
            self.solar_system.plot_solar_system_enhanced(
                date.year, date.month, date.day, view_3d=True, ax=self.ax
            )
            
            # 恢复视角
            if self.current_view is not None:
                self.ax.set_xlim(self.current_view['xlim'])
                self.ax.set_ylim(self.current_view['ylim'])
                self.ax.set_zlim(self.current_view['zlim'])
                self.ax.view_init(elev=self.current_view['elev'], azim=self.current_view['azim'])
            
            self.canvas.draw()
        except Exception as e:
            print(f"更新太阳系可视化时出现错误: {str(e)}")
            # 重置画布，下次重试
            if self.fig:
                plt.close(self.fig)
            self.fig = None
            self.canvas = None
            self.ax = None
    
    def on_motion(self, event):
        """鼠标移动事件（预留）"""
        pass
    
    def on_scroll(self, event):
        """鼠标滚轮缩放"""
        if self.ax is None:
            return
        try:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            zlim = self.ax.get_zlim()
            
            x_range = xlim[1] - xlim[0]
            y_range = ylim[1] - ylim[0]
            z_range = zlim[1] - zlim[0]
            
            scale_factor = 0.9 if event.button == 'up' else 1.1
            
            new_x_range = x_range * scale_factor
            new_y_range = y_range * scale_factor
            new_z_range = z_range * scale_factor
            
            x_center = (xlim[0] + xlim[1]) / 2
            y_center = (ylim[0] + ylim[1]) / 2
            z_center = (zlim[0] + zlim[1]) / 2
            
            self.ax.set_xlim(x_center - new_x_range/2, x_center + new_x_range/2)
            self.ax.set_ylim(y_center - new_y_range/2, y_center + new_y_range/2)
            self.ax.set_zlim(z_center - new_z_range/2, z_center + new_z_range/2)
            
            if self.canvas:
                self.canvas.draw()
        except Exception as e:
            print(f"缩放时出错: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopApp(root)
    root.mainloop()