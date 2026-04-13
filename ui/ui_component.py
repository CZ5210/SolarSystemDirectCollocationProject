import tkinter as tk
from tkinter import ttk
from datetime import datetime
from Param import TIME_CONFIG

class UIComponent:
    """UI组件类，负责创建和管理所有UI组件"""
    
    def __init__(self, root):
        self.root = root
        self.planet_list = []
        
        # 初始化所有属性
        self.main_frame = None
        self.notebook = None
        self.planning_frame = None
        self.results_frame = None
        self.control_frame = None
        self.content_frame = None
        self.viz_frame = None
        self.right_panel = None
        self.trajectory_frame = None
        self.thrust_frame = None
        self.time_slider_frame = None
        self.data_frame = None
        
        # 日期和时间相关变量
        self.current_date = datetime.now()
        self.date_var = None
        self.slider_value_var = None
        self.time_slider = None
        
        # 轨迹规划相关变量
        self.year_var = None
        self.month_var = None
        self.day_var = None
        self.departure_var = None
        self.arrival_var = None
        self.tof_days_var = None
        self.N_var = None
        self.rbound_var = None
        self.thrust_var = None
        self.maxiter_var = None
        self.guess_method_var = None
        self.calculate_button = None
        
        # 日志相关变量
        self.log_frame = None
        self.log_text = None
        self.log_collapsed = False
        self.log_toggle_button = None
        
        # 结果相关变量
        self.start_time_var = None
        self.end_time_var = None
        self.trajectory_slider = None
        self.dv_var = None
        self.max_thrust_accel_var = None
        
        # 下拉框
        self.departure_combo = None
        self.arrival_combo = None
    
    def create_ui(self):
        """创建所有界面控件"""
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
        # 配置Notebook选项卡样式
        style.configure("Dark.TNotebook", background="#2d2d2d", borderwidth=0)
        style.configure("Dark.TNotebook.Tab", 
                       background="#404040", 
                       foreground="white",
                       font=('Arial', 12, 'bold'),  # 增大字体并加粗
                       padding=[10, 5])  # 增加内边距
        style.map("Dark.TNotebook.Tab", 
                 background=[("selected", "#505050")],  # 选中时的背景色
                 foreground=[("selected", "white")])  # 选中时的前景色
        
        # 主框架
        self.main_frame = ttk.Frame(self.root, padding="10", style="Dark.TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建选项卡控件
        self.notebook = ttk.Notebook(self.main_frame, style="Dark.TNotebook")
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建规划与可视化选项卡
        self.create_plan_ui()

        # 初始化结果框架UI
        self.create_results_ui()
    
    def create_plan_ui(self):
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
        self.time_slider = ttk.Scale(self.control_frame, from_=TIME_CONFIG["min_days"], to=TIME_CONFIG["max_days"], orient=tk.HORIZONTAL, length=400, style="Dark.Horizontal.TScale")
        self.time_slider.set(TIME_CONFIG["default_days"])
        self.time_slider.pack(side=tk.LEFT, padx=10, pady=5)
        
        # 滑块值显示
        self.slider_value_var = tk.StringVar(value="0 天")
        ttk.Label(self.control_frame, textvariable=self.slider_value_var, font=('Arial', 10), style="Dark.TLabel").pack(side=tk.LEFT, padx=10, pady=5)
        
        # 内容框架：左侧可视化，右侧面板
        self.content_frame = ttk.Frame(self.planning_frame, style="Dark.TFrame")
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 使用 grid 布局来控制比例
        self.content_frame.grid_columnconfigure(0, weight=3)  # 左侧占 1 份
        self.content_frame.grid_columnconfigure(1, weight=2)  # 右侧占 1 份
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

        # 月
        ttk.Label(self.right_panel, text="月:", style="Dark.TLabel").grid(row=2, column=0, sticky=tk.W, padx=(10, 5))
        self.month_var = tk.StringVar(value=str(self.current_date.month))
        self.month_entry = ttk.Entry(self.right_panel, textvariable=self.month_var, width=10)
        self.month_entry.grid(row=2, column=1, sticky=tk.W, pady=2)

        # 日
        ttk.Label(self.right_panel, text="日:", style="Dark.TLabel").grid(row=3, column=0, sticky=tk.W, padx=(10, 5))
        self.day_var = tk.StringVar(value=str(self.current_date.day))
        self.day_entry = ttk.Entry(self.right_panel, textvariable=self.day_var, width=10)
        self.day_entry.grid(row=3, column=1, sticky=tk.W, pady=2)


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
        self.calculate_button = ttk.Button(self.right_panel, text="开始计算", style="Dark.TButton")
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
        self.log_toggle_button = ttk.Button(self.right_panel, text="折叠日志", style="Dark.TButton")
        self.log_toggle_button.grid(row=17, column=0, columnspan=2, pady=5)


    def create_results_ui(self):
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
        
        # 右侧：推力曲线面板
        self.thrust_frame = ttk.LabelFrame(self.results_frame , padding="10", style="Dark.TLabelframe")
        self.thrust_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=(5, 0), pady=(0, 10))
        self.thrust_frame.grid_columnconfigure(0, weight=1)
        self.thrust_frame.grid_rowconfigure(0, weight=1)
        
        # 推力曲线占位符
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
        self.trajectory_slider = ttk.Scale(self.time_slider_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=400, style="Dark.Horizontal.TScale")
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
    
    def set_planet_list(self, planet_list):
        """设置行星列表"""
        self.planet_list = planet_list
        # 设置下拉框的值
        if self.departure_combo and self.arrival_combo:
            self.departure_combo['values'] = self.planet_list
            self.arrival_combo['values'] = self.planet_list
            
            # 设置默认选择（如果默认值不在列表中，则选择第一个）
            if self.departure_var.get() not in self.planet_list:
                self.departure_var.set(self.planet_list[0] if self.planet_list else "")
            if self.arrival_var.get() not in self.planet_list:
                self.arrival_var.set(self.planet_list[1] if len(self.planet_list) > 1 else "")
    
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
    
    def update_date_display(self, adjusted_date, days):
        """更新日期显示"""
        self.date_var.set(f"{adjusted_date.year}-{adjusted_date.month:02d}-{adjusted_date.day:02d}")
        self.slider_value_var.set(f"{days} 天")
        
        # 更新右侧轨迹规划的出发时间
        self.year_var.set(str(adjusted_date.year))
        self.month_var.set(str(adjusted_date.month))
        self.day_var.set(str(adjusted_date.day))
    
    def update_results_display(self, dv, max_thrust_accel, start_time, end_time):
        """更新结果显示"""
        self.dv_var.set(f"ΔV: {dv:.4f} km/s")
        self.max_thrust_accel_var.set(f"最大推力加速度: {max_thrust_accel:.6f} m/s^2")
        self.start_time_var.set(f"出发时间: {start_time}")
        self.end_time_var.set(f"到达时间: {end_time}")
