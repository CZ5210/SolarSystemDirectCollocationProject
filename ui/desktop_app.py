import warnings
warnings.filterwarnings("ignore", message="3d coordinates not supported yet", category=UserWarning)

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime
import sys
import os
import shutil
import mplcursors
import threading
import queue

# 自定义stdout重定向类
class TextRedirector:
    def __init__(self, text_widget, queue):
        self.text_widget = text_widget
        self.queue = queue
        self.old_stdout = sys.stdout
    
    def write(self, string):
        self.queue.put(string)
    
    def flush(self):
        pass
    
    def __enter__(self):
        sys.stdout = self
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入参数配置
from Param import TIME_CONFIG, OUTPUT_CONFIG

class DesktopApp:
    """桌面应用类"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("太阳系轨道设计工具")
        self.root.geometry("1400x1200")
        self.root.configure(bg="#2d2d2d")
        
        # 初始化所有属性（避免 AttributeError）
        self.fig = None
        self.canvas = None
        self.ax = None
        self.current_view = None
        self.solar_system = None
        self.current_date = datetime.now()
        self.cursors = []  # 存储光标对象列表
        self._updating_from_slider = False  # 用于避免循环更新
        self.output_queue = queue.Queue()  # 用于线程间通信的队列
        
        # 第一步：清理输出目录
        self._clean_output_directory()
        
        # 第二步：创建所有 UI 控件（不依赖 core 模块）
        self._create_ui()
        
        # 第三步：设置窗口关闭时的资源清理回调
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 第四步：启动输出队列处理
        self.root.after(100, self.process_queue)
        
        # 第五步：尝试加载核心模块
        self._init_core_module()
    
    def _clean_output_directory(self):
        """清理输出目录"""
        try:
            output_dir = OUTPUT_CONFIG["directory"]
            if os.path.exists(output_dir):
                # 移除目录及其所有内容
                shutil.rmtree(output_dir)
                print(f"已清理输出目录: {output_dir}")
            # 重新创建目录结构
            os.makedirs(output_dir, exist_ok=True)
            porkchop_dir = OUTPUT_CONFIG["porkchop_directory"]
            os.makedirs(porkchop_dir, exist_ok=True)
            print(f"已创建输出目录结构")
        except Exception as e:
            print(f"清理输出目录时出错: {e}")
    
    def toggle_log(self):
        """折叠/展开日志面板"""
        if self.log_collapsed:
            # 展开日志
            self.log_frame.grid()
            self.log_toggle_button.config(text="折叠日志")
            self.log_collapsed = False
        else:
            # 折叠日志
            self.log_frame.grid_remove()
            self.log_toggle_button.config(text="展开日志")
            self.log_collapsed = True
    
    def process_queue(self):
        """处理输出队列，实时更新日志文本框"""
        try:
            while True:
                string = self.output_queue.get_nowait()
                self.log_text.insert(tk.END, string)
                self.log_text.see(tk.END)
                self.root.update_idletasks()
        except queue.Empty:
            pass
        finally:
            # 每隔100毫秒检查一次队列
            self.root.after(100, self.process_queue)
    
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
        style.configure("Dark.TEntry", fieldbackground="#404040", foreground="white")
        style.configure("Dark.TCombobox", fieldbackground="#404040", foreground="white")
        # 黑色背景样式（用于轨迹面板）
        style.configure("BlackBackground.TLabelframe", background="black", foreground="white")
        style.configure("BlackBackground.TLabelframe.Label", background="black", foreground="white")
        
        # 主框架
        self.main_frame = ttk.Frame(self.root, padding="10", style="Dark.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.main_frame, style="Dark.TFrame")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 第一个选项卡：规划与可视化
        self.planning_frame = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.planning_frame, text="规划与可视化")
        
        # 控制面板
        self.control_frame = ttk.LabelFrame(self.planning_frame, padding="10", style="Dark.TLabelframe")
        self.control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 日期显示
        self.date_var = tk.StringVar(value=f"{self.current_date.year}-{self.current_date.month:02d}-{self.current_date.day:02d}")
        ttk.Label(self.control_frame, text="当前日期:", font=('Arial', 10, 'bold'), style="Dark.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Label(self.control_frame, textvariable=self.date_var, font=('Arial', 10), style="Dark.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        
        # 时间滑块
        ttk.Label(self.control_frame, text="时间调整:", font=('Arial', 10, 'bold'), style="Dark.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        self.time_slider = ttk.Scale(self.control_frame, from_=TIME_CONFIG["min_days"], to=TIME_CONFIG["max_days"], orient=tk.HORIZONTAL, length=400, command=self.update_date, style="Dark.Horizontal.TScale")
        self.time_slider.set(TIME_CONFIG["default_days"])
        self.time_slider.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 滑块值显示
        self.slider_value_var = tk.StringVar(value="0 天")
        ttk.Label(self.control_frame, textvariable=self.slider_value_var, font=('Arial', 10), style="Dark.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        
        # 内容框架：左侧可视化，右侧面板
        self.content_frame = ttk.Frame(self.planning_frame, style="Dark.TFrame")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 使用 grid 布局来控制比例
        self.content_frame.grid_columnconfigure(0, weight=0)  # 左侧占 1 份
        self.content_frame.grid_columnconfigure(1, weight=1)  # 右侧占 1 份
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        # 左侧：太阳系可视化（保持1:1长宽比）
        self.viz_frame = ttk.LabelFrame(self.content_frame, padding="10", style="Dark.TLabelframe")
        self.viz_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 10))
        
        # 右侧：轨迹规划面板
        self.right_panel = ttk.LabelFrame(self.content_frame, padding="10", style="Dark.TLabelframe")
        self.right_panel.grid(row=0, column=1, sticky=tk.NSEW, padx=(10, 0))
        self.right_panel.grid_columnconfigure(0, weight=1)
        self.right_panel.grid_columnconfigure(1, weight=1)
        
        # 第二个选项卡：计算结果
        self.results_frame = ttk.Frame(self.notebook, style="Dark.TFrame")
        self.notebook.add(self.results_frame, text="计算结果")

        # 出发时间
        ttk.Label(self.right_panel, text="出发时间（地球时间）", font=('Arial', 10, 'bold'), style="Dark.TLabel").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))

        # 年
        ttk.Label(self.right_panel, text="年:", style="Dark.TLabel").grid(row=1, column=0, sticky=tk.W, padx=(10, 5))
        self.year_var = tk.StringVar(value=str(self.current_date.year))
        self.year_entry = ttk.Entry(self.right_panel, textvariable=self.year_var, width=10)
        self.year_entry.grid(row=1, column=1, sticky=tk.W, pady=2)
        self.year_var.trace_add("write", self.on_date_entry_change)

        # 月
        ttk.Label(self.right_panel, text="月:", style="Dark.TLabel").grid(row=2, column=0, sticky=tk.W, padx=(10, 5))
        self.month_var = tk.StringVar(value=str(self.current_date.month))
        self.month_entry = ttk.Entry(self.right_panel, textvariable=self.month_var, width=10)
        self.month_entry.grid(row=2, column=1, sticky=tk.W, pady=2)
        self.month_var.trace_add("write", self.on_date_entry_change)

        # 日
        ttk.Label(self.right_panel, text="日:", style="Dark.TLabel").grid(row=3, column=0, sticky=tk.W, padx=(10, 5))
        self.day_var = tk.StringVar(value=str(self.current_date.day))
        self.day_entry = ttk.Entry(self.right_panel, textvariable=self.day_var, width=10)
        self.day_entry.grid(row=3, column=1, sticky=tk.W, pady=2)
        self.day_var.trace_add("write", self.on_date_entry_change)


        ttk.Label(self.right_panel, text="任务规划", font=('Arial', 10, 'bold'), style="Dark.TLabel").grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))

        # 出发星体
        ttk.Label(self.right_panel, text="出发星体:", style="Dark.TLabel").grid(row=5, column=0, sticky=tk.W, padx=(10, 5))
        self.departure_var = tk.StringVar(value="地球")
        self.departure_combo = ttk.Combobox(self.right_panel, textvariable=self.departure_var, state="readonly", width=15)
        self.departure_combo.grid(row=5, column=1, sticky=tk.W, pady=2)

        # 到达星体
        ttk.Label(self.right_panel, text="到达星体:", style="Dark.TLabel").grid(row=6, column=0, sticky=tk.W, padx=(10, 5))
        self.arrival_var = tk.StringVar(value="火星")
        self.arrival_combo = ttk.Combobox(self.right_panel, textvariable=self.arrival_var, state="readonly", width=15)
        self.arrival_combo.grid(row=6, column=1, sticky=tk.W, pady=2)

        # 飞行时间（天）
        ttk.Label(self.right_panel, text="飞行时间（地球日）:", style="Dark.TLabel").grid(row=7, column=0, sticky=tk.W, padx=(10, 5), pady=(10, 5))
        self.tof_days_var = tk.StringVar(value="365")
        self.tof_days_entry = ttk.Entry(self.right_panel, textvariable=self.tof_days_var, width=10)
        self.tof_days_entry.grid(row=7, column=1, sticky=tk.W, pady=(10, 5))

        ttk.Label(self.right_panel, text="规划参数", font=('Arial', 10, 'bold'), style="Dark.TLabel").grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        # 网格数
        ttk.Label(self.right_panel, text="网格数 (N):", style="Dark.TLabel").grid(row=9, column=0, sticky=tk.W, padx=(10, 5))
        self.N_var = tk.StringVar(value="20")
        self.N_entry = ttk.Entry(self.right_panel, textvariable=self.N_var, width=10)
        self.N_entry.grid(row=9, column=1, sticky=tk.W, pady=2)

        # 最小太阳距离 (AU)
        ttk.Label(self.right_panel, text="最小太阳距离 (AU):", style="Dark.TLabel").grid(row=10, column=0, sticky=tk.W, padx=(10, 5))
        self.rbound_var = tk.StringVar(value="0.1")
        self.rbound_entry = ttk.Entry(self.right_panel, textvariable=self.rbound_var, width=10)
        self.rbound_entry.grid(row=10, column=1, sticky=tk.W, pady=2)

        # 推力限制（可选）
        ttk.Label(self.right_panel, text="推力限制 (m/s²):", style="Dark.TLabel").grid(row=11, column=0, sticky=tk.W, padx=(10, 5), pady=(5, 5))
        self.thrust_var = tk.StringVar(value="")
        self.thrust_entry = ttk.Entry(self.right_panel, textvariable=self.thrust_var, width=10)
        self.thrust_entry.grid(row=11, column=1, sticky=tk.W, pady=(5, 5))

        # 最大迭代次数
        ttk.Label(self.right_panel, text="最大迭代次数:", style="Dark.TLabel").grid(row=12, column=0, sticky=tk.W, padx=(10, 5), pady=(5, 5))
        self.maxiter_var = tk.StringVar(value="50")
        self.maxiter_entry = ttk.Entry(self.right_panel, textvariable=self.maxiter_var, width=10)
        self.maxiter_entry.grid(row=12, column=1, sticky=tk.W, pady=(5, 5))

        # 初始猜测方法
        ttk.Label(self.right_panel, text="初始猜测方法:", style="Dark.TLabel").grid(row=13, column=0, sticky=tk.W, padx=(10, 5), pady=(10, 5))
        self.guess_method_var = tk.StringVar(value="linear")
        guess_frame = ttk.Frame(self.right_panel, style="Dark.TFrame")
        guess_frame.grid(row=13, column=1, sticky=tk.W, pady=(10, 5))
        ttk.Radiobutton(guess_frame, text="线性", variable=self.guess_method_var, value="linear", style="Dark.TRadiobutton").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(guess_frame, text="椭圆", variable=self.guess_method_var, value="elliptic", style="Dark.TRadiobutton").pack(side=tk.LEFT, padx=5)

        # 开始计算按钮
        self.calculate_button = ttk.Button(self.right_panel, text="开始计算", command=self.calculate_trajectory, style="Dark.TButton")
        self.calculate_button.grid(row=14, column=0, columnspan=2, pady=20)

        # 输出日志面板
        ttk.Label(self.right_panel, text="计算日志", font=('Arial', 10, 'bold'), style="Dark.TLabel").grid(row=15, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        
        # 日志面板框架
        self.log_frame = ttk.LabelFrame(self.right_panel, padding="5", style="Dark.TLabelframe")
        self.log_frame.grid(row=16, column=0, columnspan=2, sticky=tk.NSEW, pady=5)
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(0, weight=1)
        
        # 日志文本框
        self.log_text = tk.Text(self.log_frame, height=10, wrap=tk.WORD, bg="#1e1e1e", fg="white", font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=tk.NSEW)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(self.log_frame, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=tk.NS)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 日志折叠/展开按钮
        self.log_collapsed = False
        self.log_toggle_button = ttk.Button(self.right_panel, text="折叠日志", command=self.toggle_log, style="Dark.TButton")
        self.log_toggle_button.grid(row=17, column=0, columnspan=2, pady=5)

        # 初始化行星列表（稍后在_init_core_module中填充）
        self.planet_list = []
        
        # 初始化轨迹数据属性
        self.trajectory_data = None
        self.trajectory_params = None
        self.trajectory_cursors = None
        
        # 初始化结果框架UI
        self._create_results_ui()
    
    def _create_results_ui(self):
        """创建结果框架的UI"""
        # 配置结果框架的网格布局（让轨迹面板更大）
        self.results_frame.grid_columnconfigure(0, weight=3)  # 左侧轨迹图（占3份）
        self.results_frame.grid_columnconfigure(1, weight=1)  # 右侧推力曲线（占1份）
        self.results_frame.grid_rowconfigure(0, weight=1)     # 图表区域
        self.results_frame.grid_rowconfigure(1, weight=0)     # 关键数据区域
        
        # 左侧：轨迹图面板（使用黑色背景）
        self.trajectory_frame = ttk.LabelFrame(self.results_frame, padding="10", style="Dark.TLabelframe")
        self.trajectory_frame.grid(row=0, column=0, sticky=tk.NSEW, pady=(0, 10))
        # 设置轨迹面板的背景为黑色
        self.trajectory_frame.configure(style="Dark.TLabelframe")
        self.trajectory_frame.grid_columnconfigure(0, weight=1)
        self.trajectory_frame.grid_rowconfigure(0, weight=1)
        
        # 轨迹图占位符
        self.trajectory_fig = None
        self.trajectory_canvas = None
        self.trajectory_ax = None
        
        # 右侧：推力曲线面板
        self.thrust_frame = ttk.LabelFrame(self.results_frame , padding="10", style="Dark.TLabelframe")
        self.thrust_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(5, 0), pady=(0, 10))
        self.thrust_frame.grid_columnconfigure(0, weight=1)
        self.thrust_frame.grid_rowconfigure(0, weight=1)
        
        # 推力曲线占位符
        self.thrust_fig = None
        self.thrust_canvas = None
        self.thrust_axes = None  # 四个子图的数组
        thrust_placeholder = ttk.Label(self.thrust_frame, style="Dark.TLabel")
        thrust_placeholder.pack(expand=True)
        
        # 时间滑块面板
        self.time_slider_frame = ttk.LabelFrame(self.results_frame, text="任务时间轴", padding="10", style="Dark.TLabelframe")
        self.time_slider_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 5))
        self.time_slider_frame.grid_columnconfigure(0, weight=1)
        
        # 滑块标签
        ttk.Label(self.time_slider_frame, text="时间进度:", style="Dark.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        
        # 出发时间标签
        self.start_time_var = tk.StringVar(value="出发时间: 未设置")
        ttk.Label(self.time_slider_frame, textvariable=self.start_time_var, style="Dark.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        
        # 时间滑块
        self.trajectory_slider = ttk.Scale(self.time_slider_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=400, command=self.on_trajectory_slider_change, style="Dark.Horizontal.TScale")
        self.trajectory_slider.set(0)
        self.trajectory_slider.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 到达时间标签
        self.end_time_var = tk.StringVar(value="到达时间: 未设置")
        ttk.Label(self.time_slider_frame, textvariable=self.end_time_var, style="Dark.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        
        # 底部：关键数据面板
        self.data_frame = ttk.LabelFrame(self.results_frame, text="关键数据", padding="10", style="Dark.TLabelframe")
        self.data_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=(5, 10))
        self.data_frame.grid_columnconfigure(0, weight=1)
        self.data_frame.grid_columnconfigure(1, weight=1)
        
        # 速度增量 (ΔV)
        self.dv_var = tk.StringVar(value="ΔV: 未计算")
        self.dv_label = ttk.Label(self.data_frame, textvariable=self.dv_var, font=('Arial', 12, 'bold'), style="Dark.TLabel", foreground="lightgreen")
        self.dv_label.grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        # 最大推力加速度
        self.max_thrust_accel_var = tk.StringVar(value="最大推力加速度: 未计算")
        self.max_thrust_accel_label = ttk.Label(self.data_frame, textvariable=self.max_thrust_accel_var, font=('Arial', 12, 'bold'), style="Dark.TLabel", foreground="lightgreen")
        self.max_thrust_accel_label.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # 轨迹数据存储
        self.trajectory_data = None
        self.trajectory_params = None
    
    def _init_core_module(self):
        """尝试导入并初始化 SolarSystem 模块"""
        try:
            from core.solar_system import SolarSystem
            self.solar_system = SolarSystem()
            # 初始化成功，进行首次绘图
            self.update_solar_system()
            
            # 获取行星列表（排除太阳）
            self.planet_list = [name for name in self.solar_system.bodies.keys() if name != "太阳"]
            
            # 设置下拉框的值
            self.departure_combo['values'] = self.planet_list
            self.arrival_combo['values'] = self.planet_list
            
            # 设置默认选择（如果默认值不在列表中，则选择第一个）
            if self.departure_var.get() not in self.planet_list:
                self.departure_var.set(self.planet_list[0] if self.planet_list else "")
            if self.arrival_var.get() not in self.planet_list:
                self.arrival_var.set(self.planet_list[1] if len(self.planet_list) > 1 else "")
                
        except Exception as e:
            # 显示错误并禁用时间滑块，但窗口仍然可以正常关闭
            messagebox.showerror("初始化错误", 
                f"无法加载太阳系模块：{str(e)}\n\n程序将无法显示太阳系可视化，但窗口可以正常关闭。")
            self.time_slider.config(state=tk.DISABLED)
            # 禁用轨迹规划控件
            self.disable_trajectory_controls()
            # 在可视化框架中显示错误信息
            error_label = ttk.Label(self.viz_frame, text=f"核心模块加载失败:\n{str(e)}", 
                                    style="Dark.TLabel", font=('Arial', 12))
            error_label.pack(expand=True)
    
    def disable_trajectory_controls(self):
        """禁用所有轨迹规划控件"""
        controls = [
            self.year_entry, self.month_entry, self.day_entry,
            self.departure_combo, self.arrival_combo,
            self.tof_days_entry, self.N_entry, self.rbound_entry,
            self.thrust_entry, self.calculate_button
        ]
        for control in controls:
            try:
                control.config(state=tk.DISABLED)
            except:
                pass
        print("核心模块加载失败，轨迹规划功能不可用")

    def calculate_trajectory(self):
        """计算轨迹按钮回调函数"""
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        # 输出状态到日志
        print("正在计算...")
        self.root.update_idletasks()
        
        try:
            # 验证输入
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            # 支持数学表达式计算
            tof_days_str = self.tof_days_var.get().strip()
            try:
                tof_days = float(eval(tof_days_str))
            except:
                tof_days = 365  # 默认值
            departure = self.departure_var.get()
            arrival = self.arrival_var.get()
            N = int(self.N_var.get())
            rbound = float(self.rbound_var.get())
            thrust_str = self.thrust_var.get().strip()
            thrust_limit = float(thrust_str) if thrust_str else None
            maxiter = int(self.maxiter_var.get())
            guess_method = self.guess_method_var.get()
            
            # 转换飞行时间为年（orbit_planner使用年为单位）
            tof_years = tof_days / 365.25
            
            # 导入轨道规划模块
            from features.orbit_planner import OrbitPlanner
            planner = OrbitPlanner()
            
            # 验证输入参数
            is_valid, message = planner.validate_input(
                year, month, day, tof_years, departure, arrival
            )
            if not is_valid:
                print(f"输入错误: {message}")
                return
            
            # 定义计算函数（用于线程执行）
            def calculate():
                try:
                    # 重定向stdout到日志文本框
                    with TextRedirector(self.log_text, self.output_queue):
                        # 计算轨迹（设置plot=False，避免弹出窗口）
                        dv = planner.plan_orbit(
                            start_year=year,
                            start_month=month,
                            start_day=day,
                            tof_years=tof_years,
                            departure_body=departure,
                            arrival_body=arrival,
                            N=N,
                            rbound=rbound,
                            thrust_limit=thrust_limit,
                            maxiter=maxiter,
                            guess_method=guess_method,
                            plot=False,  # 不弹出窗口
                            output_dir=OUTPUT_CONFIG["directory"]
                        )
                    
                    # 计算完成后更新UI（必须在主线程中执行）
                    def update_ui():
                        # 显示结果到日志
                        print(f"计算完成！速度增量: {dv:.4f} km/s")
                        
                        # 更新结果框架的关键数据
                        self.dv_var.set(f"ΔV: {dv:.4f} km/s")
                        # 暂时使用占位符最大推力加速度（需要从orbit_planner获取）
                        max_thrust_accel = 0.001  # 占位符
                        self.max_thrust_accel_var.set(f"最大推力加速度: {max_thrust_accel:.6f} AU/year²")
                        
                        # 切换到结果选项卡
                        self.notebook.select(1)  # 第二个选项卡
                        
                        # 更新轨迹图和推力曲线
                        self._update_trajectory_plot()
                        self._update_thrust_plots()
                    
                    # 在主线程中执行UI更新
                    self.root.after(0, update_ui)
                    
                except Exception as e:
                    def update_error():
                        print(f"计算过程中出错: {e}")
                    self.root.after(0, update_error)
            
            # 启动线程执行计算
            thread = threading.Thread(target=calculate)
            thread.daemon = True  # 守护线程，主线程退出时自动退出
            thread.start()
            
        except ValueError as e:
            print(f"输入格式错误: {e}")
        except ImportError as e:
            print(f"无法导入轨道规划模块: {e}")
        except Exception as e:
            print(f"计算过程中出错: {e}")

    def _update_trajectory_plot(self, trajectory_data=None):
        """更新转移轨迹图（使用实际计算结果）"""
        # 清除现有图形
        if self.trajectory_canvas:
            self.trajectory_canvas.get_tk_widget().destroy()
            plt.close(self.trajectory_fig)
        
        try:
            # 获取计算参数
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            # 支持数学表达式计算
            tof_days_str = self.tof_days_var.get().strip()
            try:
                tof_years = float(eval(tof_days_str)) / 365.25
            except:
                tof_years = 1.0  # 默认值
            departure = self.departure_var.get()
            arrival = self.arrival_var.get()
            
            # 生成文件名（与plan_orbit方法一致）
            file_name = f"{OUTPUT_CONFIG['directory']}/{departure}到{arrival}_{year}{month:02d}{day:02d}.csv"
            
            # 检查文件是否存在
            import os
            if not os.path.exists(file_name):
                # 如果文件不存在，使用占位符数据
                self._update_trajectory_placeholder()
                return
            
            # 读取优化结果
            import numpy as np
            solution = np.loadtxt(file_name, delimiter=',')
            N = int(self.N_var.get())
            
            # 提取轨迹数据
            x_traj = solution[:N]
            y_traj = solution[N:2*N]
            z_traj = solution[2*N:3*N]
            
            # 提取推力数据
            ux = solution[6*N:7*N]  # X方向推力
            uy = solution[7*N:8*N]  # Y方向推力
            uz = solution[8*N:9*N]  # Z方向推力
            
            # 保存轨迹数据，用于时间轴滑块
            self.trajectory_data = (x_traj, y_traj, z_traj, ux, uy, uz, N)
            self.trajectory_params = (departure, arrival, year, month, day, tof_years)
            
            # 计算到达时间
            from core.solar_system import SolarSystem
            
            solar_system = SolarSystem()
            start_jd = solar_system.date_to_julian_day(year, month, day)
            tof_days = tof_years * 365.25
            end_jd = start_jd + tof_days
            end_year, end_month, end_day = solar_system.julian_day_to_date(end_jd)
            
            # 更新时间标签
            self.start_time_var.set(f"出发时间: {year}-{month:02d}-{day:02d}")
            self.end_time_var.set(f"到达时间: {int(end_year)}-{int(end_month):02d}-{int(end_day):02d}")
            
            # 创建3D图形
            
            self.trajectory_fig = plt.figure(figsize=(8, 6), facecolor='black')
            # 移除边距，让轴域填满整个 Figure
            self.trajectory_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
            self.trajectory_ax = self.trajectory_fig.add_subplot(111, projection='3d')
            # 关闭坐标轴显示
            self.trajectory_ax.set_axis_off()
            # 设置 3D 轴的长宽比为 1:1:1，确保球体显示正确
            self.trajectory_ax.set_box_aspect((1, 1, 1))
            # 添加鼠标缩放和拖动功能
            self.trajectory_fig.canvas.mpl_connect('scroll_event', self.on_scroll)
            self.trajectory_fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
            
            # 绘制美化的太阳系作为背景
            from core.solar_system import SolarSystem
            solar_system = SolarSystem()
            # 保存轨迹图的cursor
            _, _, self.trajectory_cursors = solar_system.plot_solar_system_enhanced(year, month, day, view_3d=True, ax=self.trajectory_ax)
            
            # 绘制轨迹
            self.trajectory_ax.plot(x_traj, y_traj, z_traj, 'b-', linewidth=2, label='转移轨迹')
            
            # 绘制推力方向（控制输入）
            ux = solution[6*N:7*N]  # X方向推力
            uy = solution[7*N:8*N]  # Y方向推力
            uz = solution[8*N:9*N]  # Z方向推力
            
            # 绘制推力向量（每隔几个点绘制一个，避免过于密集）
            skip = max(1, N // 20)
            self.trajectory_ax.quiver(x_traj[::skip], y_traj[::skip], z_traj[::skip], 
                                     ux[::skip], uy[::skip], uz[::skip], 
                                     color='orange', length=0.1, normalize=True, label='推力方向')
            
            # 绘制出发点和到达点
            self.trajectory_ax.scatter([x_traj[0]], [y_traj[0]], [z_traj[0]], 
                                     color='green', marker='o', s=50, label='出发点')
            self.trajectory_ax.scatter([x_traj[-1]], [y_traj[-1]], [z_traj[-1]], 
                                     color='red', marker='o', s=50, label='到达点')
            

            
            # 设置坐标轴范围
            max_range = max(np.max(np.abs(x_traj)), np.max(np.abs(y_traj)), np.max(np.abs(z_traj)))
            self.trajectory_ax.set_xlim([-max_range, max_range])
            self.trajectory_ax.set_ylim([-max_range, max_range])
            self.trajectory_ax.set_zlim([-max_range, max_range])
            
            self.trajectory_ax.set_aspect('equal')
            
        except Exception as e:
            print(f"更新轨迹图时出错: {e}")
            # 出错时使用占位符
            self._update_trajectory_placeholder()
        
        # 嵌入到tkinter
        self.trajectory_canvas = FigureCanvasTkAgg(self.trajectory_fig, self.trajectory_frame)
        self.trajectory_canvas.draw()
        self.trajectory_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def on_trajectory_slider_change(self, value):
        """轨迹时间轴滑块变化时的回调函数"""
        if self.trajectory_data is None:
            return
        
        try:
            # 获取滑块值（0-100）
            progress = float(value) / 100.0
            
            # 获取轨迹数据
            x_traj, y_traj, z_traj, ux, uy, uz, N = self.trajectory_data
            departure, arrival, year, month, day, tof_years = self.trajectory_params
            
            # 计算当前时间（儒略日）
            from core.solar_system import SolarSystem
            solar_system = SolarSystem()
            start_jd = solar_system.date_to_julian_day(year, month, day)
            tof_days = tof_years * 365.25
            current_jd = start_jd + progress * tof_days
            
            # 计算当前日期
            current_year, current_month, current_day = solar_system.julian_day_to_date(current_jd)
            
            # 使用线性插值计算当前航天器位置和推力
            import numpy as np
            from scipy.interpolate import interp1d
            
            # 生成时间点数组（0到1）
            t = np.linspace(0, 1, N)
            
            # 创建插值函数
            interp_x = interp1d(t, x_traj, kind='linear')
            interp_y = interp1d(t, y_traj, kind='linear')
            interp_z = interp1d(t, z_traj, kind='linear')
            interp_ux = interp1d(t, ux, kind='linear')
            interp_uy = interp1d(t, uy, kind='linear')
            interp_uz = interp1d(t, uz, kind='linear')
            
            # 计算当前位置和推力
            current_x = interp_x(progress)
            current_y = interp_y(progress)
            current_z = interp_z(progress)
            current_ux = interp_ux(progress)
            current_uy = interp_uy(progress)
            current_uz = interp_uz(progress)
            
            # 检查是否已经有画布
            if self.trajectory_ax is not None:
                # 清除旧的内容
                if hasattr(self, 'trajectory_cursors') and self.trajectory_cursors:
                    for cursor in self.trajectory_cursors:
                        try:
                            cursor.remove()
                        except:
                            pass
                self.trajectory_ax.clear()
                
                # 关闭坐标轴显示
                self.trajectory_ax.set_axis_off()
                # 设置 3D 轴的长宽比为 1:1:1，确保球体显示正确
                self.trajectory_ax.set_box_aspect((1, 1, 1))
                
                # 绘制美化的太阳系作为背景（当前时间）
                # 保存轨迹图的cursor
                _, _, self.trajectory_cursors = solar_system.plot_solar_system_enhanced(int(current_year), int(current_month), int(current_day), view_3d=True, ax=self.trajectory_ax)
                
                # 绘制轨迹
                self.trajectory_ax.plot(x_traj, y_traj, z_traj, 'b-', linewidth=2, label='转移轨迹')
                
                # 绘制推力方向（控制输入）
                skip = max(1, N // 20)
                self.trajectory_ax.quiver(x_traj[::skip], y_traj[::skip], z_traj[::skip], 
                                         ux[::skip], uy[::skip], uz[::skip], 
                                         color='orange', length=0.1, normalize=True, label='推力方向')
                
                # 绘制出发点和到达点
                self.trajectory_ax.scatter([x_traj[0]], [y_traj[0]], [z_traj[0]], 
                                         color='green', marker='o', s=50, label='出发点')
                self.trajectory_ax.scatter([x_traj[-1]], [y_traj[-1]], [z_traj[-1]], 
                                         color='red', marker='o', s=50, label='到达点')
                
                # 绘制当前航天器位置（使用插值后的位置）
                self.trajectory_ax.scatter([current_x], [current_y], [current_z], 
                                         color='cyan', marker='*', s=100, label='当前位置')
                
                # 绘制当前推力方向（使用插值后的推力）
                self.trajectory_ax.quiver([current_x], [current_y], [current_z], 
                                         [current_ux], [current_uy], [current_uz], 
                                         color='yellow', length=0.2, normalize=True, label='当前推力')
                
                # 设置标题
                self.trajectory_ax.set_title(f'{departure}到{arrival}的转移轨迹\n当前时间: {int(current_year)}-{int(current_month):02d}-{int(current_day):02d}', color='white')
                
                # 设置坐标轴范围
                max_range = max(np.max(np.abs(x_traj)), np.max(np.abs(y_traj)), np.max(np.abs(z_traj)))
                self.trajectory_ax.set_xlim([-max_range, max_range])
                self.trajectory_ax.set_ylim([-max_range, max_range])
                self.trajectory_ax.set_zlim([-max_range, max_range])
                
                self.trajectory_ax.set_aspect('equal')
                
                # 刷新画布
                if self.trajectory_canvas:
                    self.trajectory_canvas.draw()
            else:
                # 如果没有画布，创建新的（首次运行时）
                # 创建3D图形
                self.trajectory_fig = plt.figure(figsize=(8, 6), facecolor='black')
                # 移除边距，让轴域填满整个 Figure
                self.trajectory_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
                self.trajectory_ax = self.trajectory_fig.add_subplot(111, projection='3d')
                # 关闭坐标轴显示
                self.trajectory_ax.set_axis_off()
                # 设置 3D 轴的长宽比为 1:1:1，确保球体显示正确
                self.trajectory_ax.set_box_aspect((1, 1, 1))
                # 添加鼠标缩放和拖动功能
                self.trajectory_fig.canvas.mpl_connect('scroll_event', self.on_scroll)
                self.trajectory_fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
                
                # 绘制美化的太阳系作为背景（当前时间）
                # 保存轨迹图的cursor
                _, _, self.trajectory_cursors = solar_system.plot_solar_system_enhanced(int(current_year), int(current_month), int(current_day), view_3d=True, ax=self.trajectory_ax)
                
                # 绘制轨迹
                self.trajectory_ax.plot(x_traj, y_traj, z_traj, 'b-', linewidth=2, label='转移轨迹')
                
                # 绘制推力方向（控制输入）
                skip = max(1, N // 20)
                self.trajectory_ax.quiver(x_traj[::skip], y_traj[::skip], z_traj[::skip], 
                                         ux[::skip], uy[::skip], uz[::skip], 
                                         color='orange', length=0.1, normalize=True, label='推力方向')
                
                # 绘制出发点和到达点
                self.trajectory_ax.scatter([x_traj[0]], [y_traj[0]], [z_traj[0]], 
                                         color='green', marker='o', s=50, label='出发点')
                self.trajectory_ax.scatter([x_traj[-1]], [y_traj[-1]], [z_traj[-1]], 
                                         color='red', marker='o', s=50, label='到达点')
                
                # 绘制当前航天器位置（使用插值后的位置）
                self.trajectory_ax.scatter([current_x], [current_y], [current_z], 
                                         color='cyan', marker='*', s=100, label='当前位置')
                
                # 绘制当前推力方向（使用插值后的推力）
                self.trajectory_ax.quiver([current_x], [current_y], [current_z], 
                                         [current_ux], [current_uy], [current_uz], 
                                         color='yellow', length=0.2, normalize=True, label='当前推力')
                
                # 设置标题
                self.trajectory_ax.set_title(f'{departure}到{arrival}的转移轨迹\n当前时间: {int(current_year)}-{int(current_month):02d}-{int(current_day):02d}', color='white')
                
                # 设置坐标轴范围
                max_range = max(np.max(np.abs(x_traj)), np.max(np.abs(y_traj)), np.max(np.abs(z_traj)))
                self.trajectory_ax.set_xlim([-max_range, max_range])
                self.trajectory_ax.set_ylim([-max_range, max_range])
                self.trajectory_ax.set_zlim([-max_range, max_range])
                
                self.trajectory_ax.set_aspect('equal')
                
                # 嵌入到tkinter
                self.trajectory_canvas = FigureCanvasTkAgg(self.trajectory_fig, self.trajectory_frame)
                self.trajectory_canvas.draw()
                self.trajectory_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
        except Exception as e:
            print(f"更新轨迹时间轴时出错: {e}")
        
    
    def _update_thrust_plots(self, thrust_data=None):
        """更新推力曲线图（使用实际计算结果）"""
        # 清除现有图形
        if self.thrust_canvas:
            self.thrust_canvas.get_tk_widget().destroy()
            plt.close(self.thrust_fig)
        
        try:
            # 获取计算参数
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            # 支持数学表达式计算
            tof_days_str = self.tof_days_var.get().strip()
            try:
                tof_years = float(eval(tof_days_str)) / 365.25
            except:
                tof_years = 1.0  # 默认值
            departure = self.departure_var.get()
            arrival = self.arrival_var.get()
            
            # 生成文件名（与plan_orbit方法一致）
            file_name = f"{OUTPUT_CONFIG['directory']}/{departure}到{arrival}_{year}{month:02d}{day:02d}.csv"
            
            # 检查文件是否存在
            import os
            if not os.path.exists(file_name):
                # 如果文件不存在，使用占位符数据
                self._update_thrust_placeholder()
                return
            
            # 读取优化结果
            import numpy as np
            solution = np.loadtxt(file_name, delimiter=',')
            N = int(self.N_var.get())
            
            # 提取位置数据
            x = solution[0:N]  # X方向位置 (AU)
            y = solution[N:2*N]  # Y方向位置 (AU)
            z = solution[2*N:3*N]  # Z方向位置 (AU)
            
            # 提取速度数据
            vx = solution[3*N:4*N]  # X方向速度
            vy = solution[4*N:5*N]  # Y方向速度
            vz = solution[5*N:6*N]  # Z方向速度
            
            # 提取控制输入数据（推力）
            ux = solution[6*N:7*N]  # X方向推力
            uy = solution[7*N:8*N]  # Y方向推力
            uz = solution[8*N:9*N]  # Z方向推力

            # 将加速度从AU/year^2转换为m/s^2
            ux = ux * (149597871 / ((365.25*24*3600)**2))*1000
            uy = uy * (149597871 / ((365.25*24*3600)**2))*1000
            uz = uz * (149597871 / ((365.25*24*3600)**2))*1000
            
            # 计算总推力
            thrust_mag = np.sqrt(ux**2 + uy**2 + uz**2)
            
            # 计算速度大小（从AU/year转换为km/s）
            vx_km_s = vx * 149597871 / (365.25*24*3600)
            vy_km_s = vy * 149597871 / (365.25*24*3600)
            vz_km_s = vz * 149597871 / (365.25*24*3600)
            speed_mag = np.sqrt(vx_km_s**2 + vy_km_s**2 + vz_km_s**2)

            # 生成时间数据（天）
            tof_days = tof_years * 365.25
            t = np.linspace(0, tof_days, N)
            
            # 计算飞船与各星体之间的距离（AU）
            if self.solar_system is None:
                from core.solar_system import SolarSystem
                self.solar_system = SolarSystem()
            
            distances = {}  # 存储每个星体的距离数组
            import datetime
            # 预先计算每个时间点的儒略日
            jds = np.zeros(N)
            for i in range(N):
                current_date = datetime.date(year, month, day) + datetime.timedelta(days=t[i])
                jds[i] = self.solar_system.date_to_julian_day(current_date.year, current_date.month, current_date.day)
            # 计算每个星体的距离
            for body_name in self.solar_system.bodies.keys():
                body_distances = np.zeros(N)
                for i in range(N):
                    # 使用儒略日计算星体位置
                    bx, by, bz = self.solar_system.calculate_body_position(body_name, julian_day=jds[i])
                    # 计算距离
                    body_distances[i] = np.sqrt((x[i] - bx)**2 + (y[i] - by)**2 + (z[i] - bz)**2)
                distances[body_name] = body_distances
            
            # 计算最大推力加速度
            max_thrust_accel = np.max(thrust_mag)
            self.max_thrust_accel_var.set(f"最大推力加速度: {max_thrust_accel:.6f} m/s^2")
            
            # 创建包含6个子图的图形（6行1列）
            self.thrust_fig, self.thrust_axes = plt.subplots(6, 1, figsize=(8, 14))
            self.thrust_fig.patch.set_facecolor('#2d2d2d')
            
            # 子图1：X方向推力
            ax1 = self.thrust_axes[0]
            ax1.set_facecolor('#2d2d2d')
            ax1.plot(t, ux, 'r-', linewidth=2)
            ax1.set_ylabel(r'推力 X $m/s^2$', color='white')
            ax1.tick_params(colors='white')
            ax1.grid(True, alpha=0.3)
            
            # 子图2：Y方向推力
            ax2 = self.thrust_axes[1]
            ax2.set_facecolor('#2d2d2d')
            ax2.plot(t, uy, 'g-', linewidth=2)
            ax2.set_ylabel(r'推力 Y $m/s^2$', color='white')
            ax2.tick_params(colors='white')
            ax2.grid(True, alpha=0.3)
            
            # 子图3：Z方向推力
            ax3 = self.thrust_axes[2]
            ax3.set_facecolor('#2d2d2d')
            ax3.plot(t, uz, 'b-', linewidth=2)
            ax3.set_ylabel(r'推力 Z $m/s^2$', color='white')
            ax3.tick_params(colors='white')
            ax3.grid(True, alpha=0.3)
            
            # 子图4：总推力
            ax4 = self.thrust_axes[3]
            ax4.set_facecolor('#2d2d2d')
            ax4.plot(t, thrust_mag, 'm-', linewidth=2)
            ax4.set_ylabel(r'总推力 $m/s^2$', color='white')
            ax4.tick_params(colors='white')
            ax4.grid(True, alpha=0.3)
            
            # 子图5：速度大小
            ax5 = self.thrust_axes[4]
            ax5.set_facecolor('#2d2d2d')
            ax5.plot(t, speed_mag, 'c-', linewidth=2)
            ax5.set_ylabel(r'速度大小 $km/s$', color='white')
            ax5.tick_params(colors='white')
            ax5.grid(True, alpha=0.3)
            
            # 添加参考速度线
            max_speed = np.max(speed_mag)
            
            # 太阳系逃逸速度（地球轨道附近）约42.1 km/s
            escape_velocity = 42.1
            # 0.14光速
            light_speed_014 = 0.14 * 299792  # 约41970 km/s
            
            # 只有当最大速度超过这些值时才绘制参考线
            if max_speed > escape_velocity:
                ax5.axhline(y=escape_velocity, color='y', linestyle='--', linewidth=1, label=f'太阳系逃逸速度: {escape_velocity} km/s')
            
            if max_speed > light_speed_014:
                ax5.axhline(y=light_speed_014, color='r', linestyle='--', linewidth=1, label=f'0.14光速: {light_speed_014:.0f} km/s')
            
            # 添加图例
            if max_speed > escape_velocity or max_speed > light_speed_014:
                ax5.legend(loc='upper left', fontsize=8, facecolor='#2d2d2d', edgecolor='white', labelcolor='white')
            
            # 子图6：与各星体距离,如果不在1AU内,则不绘制该星体曲线
            ax6 = self.thrust_axes[5]
            ax6.set_facecolor('#2d2d2d')
            # 绘制每条距离曲线,y轴对数缩放
            for body_name in self.solar_system.bodies.keys():
                # 如果距离在1AU内,则不绘制
                if np.min(distances[body_name]) > 1.0:
                    continue
                # 绘制距离曲线
                color = self.solar_system.bodies[body_name]['color']
                ax6.plot(t, distances[body_name], color=color, linewidth=1, label=body_name)
            ax6.set_xlabel('时间 (天)', color='white')
            ax6.set_ylabel(r'距离 $AU$', color='white')
            ax6.set_ylim(0,1)
            ax6.tick_params(colors='white')
            ax6.grid(True, alpha=0.3)

            ax6.legend(loc='upper left',fontsize=8, facecolor='#2d2d2d', edgecolor='white', labelcolor='white')
            
            # 调整布局
            self.thrust_fig.tight_layout()
            
        except Exception as e:
            print(f"更新推力曲线时出错: {e}")
            # 出错时使用占位符
            self._update_thrust_placeholder()
        
        # 嵌入到tkinter
        self.thrust_canvas = FigureCanvasTkAgg(self.thrust_fig, self.thrust_frame)
        self.thrust_canvas.draw()
        self.thrust_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def on_closing(self):
        """窗口关闭时清理 Matplotlib 资源并退出"""
        try:
            # 关闭所有 matplotlib 图形
            plt.close('all')
            # 销毁画布部件
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            if self.trajectory_canvas:
                self.trajectory_canvas.get_tk_widget().destroy()
            if self.thrust_canvas:
                self.thrust_canvas.get_tk_widget().destroy()
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
            # 确保时间只能前进，不能后退
            current_days = int(self.time_slider.get())
            if days < current_days:
                # 如果尝试后退，保持当前值
                self.time_slider.set(current_days)
                return
            
            adjusted_date = self.current_date.replace(hour=0, minute=0, second=0, microsecond=0)
            adjusted_date = adjusted_date.fromordinal(adjusted_date.toordinal() + days)
            
            # 更新界面控件（它们一定存在，因为 UI 已先创建）
            self.date_var.set(f"{adjusted_date.year}-{adjusted_date.month:02d}-{adjusted_date.day:02d}")
            self.slider_value_var.set(f"{days} 天")
            
            # 更新右侧轨迹规划的出发时间（暂时禁用回调，避免循环更新）
            self._updating_from_slider = True
            try:
                self.year_var.set(str(adjusted_date.year))
                self.month_var.set(str(adjusted_date.month))
                self.day_var.set(str(adjusted_date.day))
            finally:
                self._updating_from_slider = False
            
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
                
                # 使用固定大小的 figure（10x10 英寸，1:1 长宽比）
                self.fig = plt.figure(figsize=(10, 10), facecolor='black')
                # 移除边距，让轴域填满整个 Figure
                self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
                self.ax = self.fig.add_subplot(111, projection='3d')
                # 关闭轴的裁剪，使轨道线即使在视图外也能完整绘制
                self.ax.set_axis_off()  # 关闭坐标轴显示
                # 设置 3D 轴的长宽比为 1:1:1，确保球体显示正确
                self.ax.set_box_aspect((1, 1, 1))
                self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
                self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
                self.canvas = FigureCanvasTkAgg(self.fig, master=self.viz_frame)
                self.canvas.draw()
                self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            else:
                # 清理旧的光标对象
                if hasattr(self, 'cursors') and self.cursors:
                    for cursor in self.cursors:
                        try:
                            cursor.remove()
                        except:
                            pass
                self.ax.clear()
                # 重新设置轴的属性
                self.ax.set_axis_off()
                self.ax.set_box_aspect((1, 1, 1))
            
            # 调用核心绘图函数
            _, _, self.cursors = self.solar_system.plot_solar_system_enhanced(
                date.year, date.month, date.day, view_3d=True, ax=self.ax
            )
            
            # 恢复视角
            if self.current_view is not None:
                self.ax.set_xlim(self.current_view['xlim'])
                self.ax.set_ylim(self.current_view['ylim'])
                self.ax.set_zlim(self.current_view['zlim'])
                self.ax.view_init(elev=self.current_view['elev'], azim=self.current_view['azim'])
            
            # 刷新画布
            self.canvas.draw()
        except Exception as e:
            print(f"更新太阳系可视化时出现错误: {str(e)}")
            # 重置画布，下次重试
            if self.fig:
                plt.close(self.fig)
            self.fig = None
            self.canvas = None
            self.ax = None
    

    
    def on_date_entry_change(self, *args):
        """出发时间输入框变化时的回调函数"""
        # 如果核心模块未就绪，不做任何操作
        if self.solar_system is None:
            return
        
        # 如果是从滑块更新触发的，避免循环更新
        if getattr(self, '_updating_from_slider', False):
            return
        
        try:
            # 获取输入的日期
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            day = int(self.day_var.get())
            
            # 验证日期有效性
            from features.orbit_planner import OrbitPlanner
            planner = OrbitPlanner()
            is_valid, message = planner.validate_input(year, month, day, 1, "地球", "火星")
            if not is_valid:
                return
            
            # 计算与当前日期的天数差
            import datetime
            entry_date = datetime.date(year, month, day)
            current_date = self.current_date.date()
            days_diff = (entry_date - current_date).days
            
            # 更新日期显示
            self.date_var.set(f"{year}-{month:02d}-{day:02d}")
            
            # 只有当时间在滑块范围内（非负数）时才更新滑块
            if days_diff >= 0:
                self.time_slider.set(days_diff)
                self.slider_value_var.set(f"{days_diff} 天")
            else:
                # 对于过去的时间，不更新滑块，但仍然更新可视化
                self.slider_value_var.set(f"{days_diff} 天 (过去)")
            
            # 更新可视化（无论时间是否在滑块范围内）
            self.update_solar_system(datetime.datetime(year, month, day))
            
        except ValueError:
            # 输入格式错误，忽略
            pass
        except Exception as e:
            print(f"更新日期输入时出现错误: {str(e)}")

    def on_motion(self, event):
        """鼠标移动事件：移除悬停注解"""
        # 当鼠标移动时，隐藏所有悬停注解
        if event.inaxes:  # 鼠标在坐标轴内
            # 清除主太阳系视图的cursor
            if hasattr(self, 'cursors') and self.cursors:
                for cursor in self.cursors:
                    try:
                        if cursor.selections:
                            for sel in cursor.selections:
                                if hasattr(sel, 'annotation') and sel.annotation:
                                    sel.annotation.set_visible(False)
                    except:
                        pass
            
            # 清除轨迹视图的cursor（如果有）
            if hasattr(self, 'trajectory_cursors') and self.trajectory_cursors:
                for cursor in self.trajectory_cursors:
                    try:
                        if cursor.selections:
                            for sel in cursor.selections:
                                if hasattr(sel, 'annotation') and sel.annotation:
                                    sel.annotation.set_visible(False)
                    except:
                        pass
    
    def on_scroll(self, event):
        """鼠标滚轮缩放"""
        # 尝试获取当前活动的轴
        ax = None
        canvas = None
        
        # 检查是否是轨迹图的事件
        if hasattr(self, 'trajectory_ax') and self.trajectory_ax:
            # 检查事件是否来自轨迹图的画布
            if hasattr(self, 'trajectory_canvas') and self.trajectory_canvas:
                if event.inaxes == self.trajectory_ax:
                    ax = self.trajectory_ax
                    canvas = self.trajectory_canvas
        
        # 如果不是轨迹图的事件，使用主太阳系视图的轴
        if ax is None and hasattr(self, 'ax') and self.ax:
            if event.inaxes == self.ax:
                ax = self.ax
                canvas = self.canvas
        
        if ax is None:
            return
        
        try:
            xlim = ax.get_xlim()
            ylim = ax.get_ylim()
            zlim = ax.get_zlim()
            
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
            
            ax.set_xlim(x_center - new_x_range/2, x_center + new_x_range/2)
            ax.set_ylim(y_center - new_y_range/2, y_center + new_y_range/2)
            ax.set_zlim(z_center - new_z_range/2, z_center + new_z_range/2)
            
            # 清除所有悬停注解
            # 清除主太阳系视图的cursor
            if hasattr(self, 'cursors') and self.cursors:
                for i, cursor in enumerate(self.cursors):
                    try:
                        # 如果有活动选择，隐藏注解而不是调用remove()
                        if cursor.selections:
                            for sel in cursor.selections:
                                if hasattr(sel, 'annotation') and sel.annotation:
                                    sel.annotation.set_visible(False)
                        else:
                            # 没有活动选择，尝试调用remove()但可能会影响后续悬停
                            # 暂时不调用remove，因为可能导致光标失效
                            pass
                    except Exception as e:
                        print(f"[DEBUG] 光标 {i} 处理失败: {e}")
            
            # 清除轨迹视图的cursor（如果有）
            if hasattr(self, 'trajectory_cursors') and self.trajectory_cursors:
                for i, cursor in enumerate(self.trajectory_cursors):
                    try:
                        # 如果有活动选择，隐藏注解而不是调用remove()
                        if cursor.selections:
                            for sel in cursor.selections:
                                if hasattr(sel, 'annotation') and sel.annotation:
                                    sel.annotation.set_visible(False)
                        else:
                            # 没有活动选择，尝试调用remove()但可能会影响后续悬停
                            # 暂时不调用remove，因为可能导致光标失效
                            pass
                    except Exception as e:
                        print(f"[DEBUG] 轨迹光标 {i} 处理失败: {e}")
            
            if canvas:
                canvas.draw()
        except Exception as e:
            print(f"缩放时出错: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopApp(root)
    root.mainloop()
