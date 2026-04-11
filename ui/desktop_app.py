import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from datetime import datetime
from features.orbit_planner import OrbitPlanner
from features.porkchop import Porkchop
from features.direction_optimizer import DirectionOptimizer
from core.solar_system import SolarSystem

class DesktopApp:
    """桌面应用类"""
    
    def __init__(self, root):
        """
        初始化桌面应用
        :param root: tkinter根窗口
        """
        self.root = root
        self.root.title("太阳系轨道设计工具")
        self.root.geometry("1200x800")
        
        # 获取当前日期
        self.current_date = datetime.now()
        
        # 创建功能模块实例
        self.planner = OrbitPlanner()
        self.porkchop = Porkchop()
        self.direction_optimizer = DirectionOptimizer()
        self.solar_system = SolarSystem()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标签页
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建轨道规划标签页
        self.orbit_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.orbit_frame, text="轨道规划")
        
        # 创建猪排图标签页
        self.porkchop_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.porkchop_frame, text="发射窗口分析")
        
        # 创建方向优化标签页
        self.direction_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.direction_frame, text="方向优化")
        
        # 创建太阳系可视化标签页
        self.solar_system_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.solar_system_frame, text="太阳系可视化")
        
        # 初始化各标签页
        self.init_orbit_frame()
        self.init_porkchop_frame()
        self.init_direction_frame()
        self.init_solar_system_frame()
    
    def init_orbit_frame(self):
        """初始化轨道规划标签页"""
        # 创建参数设置框架
        param_frame = ttk.LabelFrame(self.orbit_frame, text="轨道参数设置", padding="10")
        param_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 网格布局
        grid_frame = ttk.Frame(param_frame)
        grid_frame.pack(fill=tk.X)
        
        # 出发日期
        ttk.Label(grid_frame, text="出发年份:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.start_year_var = tk.StringVar(value=str(self.current_date.year))
        ttk.Entry(grid_frame, textvariable=self.start_year_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(grid_frame, text="月份:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.start_month_var = tk.StringVar(value=str(self.current_date.month))
        ttk.Entry(grid_frame, textvariable=self.start_month_var, width=5).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(grid_frame, text="日期:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.start_day_var = tk.StringVar(value=str(self.current_date.day))
        ttk.Entry(grid_frame, textvariable=self.start_day_var, width=5).grid(row=0, column=5, padx=5, pady=5)
        
        # 飞行时间
        ttk.Label(grid_frame, text="飞行时间(年):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.tof_years_var = tk.StringVar(value="2")
        ttk.Entry(grid_frame, textvariable=self.tof_years_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        # 出发星体
        ttk.Label(grid_frame, text="出发星体:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.departure_body_var = tk.StringVar(value="木星")
        departure_bodies = self.planner.get_planet_list()
        ttk.Combobox(grid_frame, textvariable=self.departure_body_var, values=departure_bodies, width=15).grid(row=2, column=1, padx=5, pady=5)
        
        # 到达星体
        ttk.Label(grid_frame, text="到达星体:").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        self.arrival_body_var = tk.StringVar(value="海王星")
        arrival_bodies = self.planner.get_planet_list()
        ttk.Combobox(grid_frame, textvariable=self.arrival_body_var, values=arrival_bodies, width=15).grid(row=2, column=3, padx=5, pady=5)
        
        # 网格数
        ttk.Label(grid_frame, text="网格数:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.N_var = tk.StringVar(value="50")
        ttk.Entry(grid_frame, textvariable=self.N_var, width=10).grid(row=3, column=1, padx=5, pady=5)
        
        # 半径边界因子
        ttk.Label(grid_frame, text="太阳距离约束因子:").grid(row=3, column=2, padx=5, pady=5, sticky=tk.W)
        self.rbound_factor_var = tk.StringVar(value="0.5")
        ttk.Entry(grid_frame, textvariable=self.rbound_factor_var, width=10).grid(row=3, column=3, padx=5, pady=5)
        
        # 推力限制
        ttk.Label(grid_frame, text="推力限制(AU/year²):").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.thrust_limit_var = tk.StringVar(value="")
        ttk.Entry(grid_frame, textvariable=self.thrust_limit_var, width=10).grid(row=4, column=1, padx=5, pady=5)
        ttk.Label(grid_frame, text="(留空表示无限制)").grid(row=4, column=2, padx=5, pady=5, sticky=tk.W)
        
        # 计算按钮
        ttk.Button(param_frame, text="计算轨道", command=self.calculate_orbit).pack(pady=10)
        
        # 结果展示框架
        result_frame = ttk.LabelFrame(self.orbit_frame, text="计算结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 速度增量显示
        ttk.Label(result_frame, text="速度增量(km/s):").pack(anchor=tk.W, pady=5)
        self.dv_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=self.dv_var, font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=5)
        
        # 可视化框架
        viz_frame = ttk.LabelFrame(result_frame, text="轨迹可视化", padding="10")
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 绘制轨迹按钮
        ttk.Button(viz_frame, text="绘制轨迹", command=self.plot_trajectory).pack(pady=5)
        
        # 结果图片标签
        self.result_image_label = ttk.Label(viz_frame)
        self.result_image_label.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def init_porkchop_frame(self):
        """初始化猪排图标签页"""
        # 创建参数设置框架
        param_frame = ttk.LabelFrame(self.porkchop_frame, text="猪排图参数设置", padding="10")
        param_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 网格布局
        grid_frame = ttk.Frame(param_frame)
        grid_frame.pack(fill=tk.X)
        
        # 出发星体
        ttk.Label(grid_frame, text="出发星体:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.porkchop_departure_var = tk.StringVar(value="木星")
        departure_bodies = self.planner.get_planet_list()
        ttk.Combobox(grid_frame, textvariable=self.porkchop_departure_var, values=departure_bodies, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        # 到达星体
        ttk.Label(grid_frame, text="到达星体:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.porkchop_arrival_var = tk.StringVar(value="海王星")
        arrival_bodies = self.planner.get_planet_list()
        ttk.Combobox(grid_frame, textvariable=self.porkchop_arrival_var, values=arrival_bodies, width=15).grid(row=0, column=3, padx=5, pady=5)
        
        # 年份范围
        ttk.Label(grid_frame, text="起始年份:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.porkchop_start_year_var = tk.StringVar(value="2300")
        ttk.Entry(grid_frame, textvariable=self.porkchop_start_year_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(grid_frame, text="结束年份:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.porkchop_end_year_var = tk.StringVar(value="2350")
        ttk.Entry(grid_frame, textvariable=self.porkchop_end_year_var, width=10).grid(row=1, column=3, padx=5, pady=5)
        
        # 飞行时间范围
        ttk.Label(grid_frame, text="飞行时间范围(年):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.porkchop_tof_min_var = tk.StringVar(value="1")
        ttk.Entry(grid_frame, textvariable=self.porkchop_tof_min_var, width=5).grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(grid_frame, text="-").grid(row=2, column=2, padx=5, pady=5)
        self.porkchop_tof_max_var = tk.StringVar(value="10")
        ttk.Entry(grid_frame, textvariable=self.porkchop_tof_max_var, width=5).grid(row=2, column=3, padx=5, pady=5)
        
        # 网格数
        ttk.Label(grid_frame, text="网格数:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.porkchop_N_var = tk.StringVar(value="30")
        ttk.Entry(grid_frame, textvariable=self.porkchop_N_var, width=10).grid(row=3, column=1, padx=5, pady=5)
        
        # 计算按钮
        ttk.Button(param_frame, text="计算发射窗口", command=self.calculate_porkchop).pack(pady=10)
        
        # 结果展示框架
        result_frame = ttk.LabelFrame(self.porkchop_frame, text="猪排图", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 绘制猪排图按钮
        ttk.Button(result_frame, text="绘制猪排图", command=self.plot_porkchop).pack(pady=5)
        
        # 结果图片标签
        self.porkchop_image_label = ttk.Label(result_frame)
        self.porkchop_image_label.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def init_direction_frame(self):
        """初始化方向优化标签页"""
        # 创建参数设置框架
        param_frame = ttk.LabelFrame(self.direction_frame, text="方向优化参数设置", padding="10")
        param_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 网格布局
        grid_frame = ttk.Frame(param_frame)
        grid_frame.pack(fill=tk.X)
        
        # 出发日期
        ttk.Label(grid_frame, text="出发年份:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.dir_start_year_var = tk.StringVar(value=str(self.current_date.year))
        ttk.Entry(grid_frame, textvariable=self.dir_start_year_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(grid_frame, text="月份:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.dir_start_month_var = tk.StringVar(value=str(self.current_date.month))
        ttk.Entry(grid_frame, textvariable=self.dir_start_month_var, width=5).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(grid_frame, text="日期:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.dir_start_day_var = tk.StringVar(value=str(self.current_date.day))
        ttk.Entry(grid_frame, textvariable=self.dir_start_day_var, width=5).grid(row=0, column=5, padx=5, pady=5)
        
        # 飞行时间
        ttk.Label(grid_frame, text="飞行时间(年):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.dir_tof_years_var = tk.StringVar(value="2")
        ttk.Entry(grid_frame, textvariable=self.dir_tof_years_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        # 出发星体
        ttk.Label(grid_frame, text="出发星体:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.dir_departure_body_var = tk.StringVar(value="木星")
        departure_bodies = self.planner.get_planet_list()
        ttk.Combobox(grid_frame, textvariable=self.dir_departure_body_var, values=departure_bodies, width=15).grid(row=2, column=1, padx=5, pady=5)
        
        # 到达星体
        ttk.Label(grid_frame, text="到达星体:").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        self.dir_arrival_body_var = tk.StringVar(value="海王星")
        arrival_bodies = self.planner.get_planet_list()
        ttk.Combobox(grid_frame, textvariable=self.dir_arrival_body_var, values=arrival_bodies, width=15).grid(row=2, column=3, padx=5, pady=5)
        
        # 网格数
        ttk.Label(grid_frame, text="网格数:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.dir_N_var = tk.StringVar(value="30")
        ttk.Entry(grid_frame, textvariable=self.dir_N_var, width=10).grid(row=3, column=1, padx=5, pady=5)
        
        # 优化类型
        ttk.Label(grid_frame, text="优化类型:").grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)
        self.optimize_type_var = tk.StringVar(value="出发方向")
        ttk.Combobox(grid_frame, textvariable=self.optimize_type_var, 
                    values=["出发方向", "到达方向", "同时优化"], width=15).grid(row=4, column=1, padx=5, pady=5)
        
        # 计算按钮
        ttk.Button(param_frame, text="优化方向", command=self.optimize_direction).pack(pady=10)
        
        # 结果展示框架
        result_frame = ttk.LabelFrame(self.direction_frame, text="优化结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 结果显示
        self.direction_result_var = tk.StringVar(value="")
        ttk.Label(result_frame, textvariable=self.direction_result_var, font=('Arial', 10)).pack(anchor=tk.W, pady=5)
    
    def init_solar_system_frame(self):
        """初始化太阳系可视化标签页"""
        # 创建参数设置框架
        param_frame = ttk.LabelFrame(self.solar_system_frame, text="太阳系可视化参数", padding="10")
        param_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 网格布局
        grid_frame = ttk.Frame(param_frame)
        grid_frame.pack(fill=tk.X)
        
        # 日期设置
        ttk.Label(grid_frame, text="年份:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.ss_year_var = tk.StringVar(value="2300")
        ttk.Entry(grid_frame, textvariable=self.ss_year_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(grid_frame, text="月份:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.ss_month_var = tk.StringVar(value="1")
        ttk.Entry(grid_frame, textvariable=self.ss_month_var, width=5).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(grid_frame, text="日期:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.ss_day_var = tk.StringVar(value="1")
        ttk.Entry(grid_frame, textvariable=self.ss_day_var, width=5).grid(row=0, column=5, padx=5, pady=5)
        
        # 视图类型
        ttk.Label(grid_frame, text="视图类型:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.view_type_var = tk.StringVar(value="3D")
        ttk.Combobox(grid_frame, textvariable=self.view_type_var, values=["2D", "3D"], width=10).grid(row=1, column=1, padx=5, pady=5)
        
        # 绘制按钮
        ttk.Button(param_frame, text="绘制太阳系", command=self.plot_solar_system).pack(pady=10)
        
        # 可视化框架
        viz_frame = ttk.LabelFrame(self.solar_system_frame, text="太阳系可视化", padding="10")
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 结果图片标签
        self.ss_image_label = ttk.Label(viz_frame)
        self.ss_image_label.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def calculate_orbit(self):
        """计算轨道"""
        try:
            # 获取参数
            start_year = int(self.start_year_var.get())
            start_month = int(self.start_month_var.get())
            start_day = int(self.start_day_var.get())
            tof_years = float(self.tof_years_var.get())
            departure_body = self.departure_body_var.get()
            arrival_body = self.arrival_body_var.get()
            N = int(self.N_var.get())
            rbound_factor = float(self.rbound_factor_var.get())
            
            # 处理推力限制
            thrust_limit = self.thrust_limit_var.get()
            if thrust_limit:
                thrust_limit = float(thrust_limit)
            else:
                thrust_limit = None
            
            # 验证输入
            is_valid, message = self.planner.validate_input(
                start_year, start_month, start_day, tof_years, departure_body, arrival_body
            )
            if not is_valid:
                messagebox.showerror("输入错误", message)
                return
            
            # 计算轨道
            dv = self.planner.plan_orbit(
                start_year=start_year,
                start_month=start_month,
                start_day=start_day,
                tof_years=tof_years,
                departure_body=departure_body,
                arrival_body=arrival_body,
                N=N,
                rbound_factor=rbound_factor,
                thrust_limit=thrust_limit,
                plot=False
            )
            
            # 显示结果
            self.dv_var.set(f"{dv:.4f}")
            messagebox.showinfo("计算完成", f"轨道计算完成，速度增量: {dv:.4f} km/s")
            
        except Exception as e:
            messagebox.showerror("计算错误", f"计算过程中出现错误: {str(e)}")
    
    def plot_trajectory(self):
        """绘制轨迹"""
        try:
            # 获取参数
            start_year = int(self.start_year_var.get())
            start_month = int(self.start_month_var.get())
            start_day = int(self.start_day_var.get())
            tof_years = float(self.tof_years_var.get())
            departure_body = self.departure_body_var.get()
            arrival_body = self.arrival_body_var.get()
            N = int(self.N_var.get())
            rbound_factor = float(self.rbound_factor_var.get())
            
            # 处理推力限制
            thrust_limit = self.thrust_limit_var.get()
            if thrust_limit:
                thrust_limit = float(thrust_limit)
            else:
                thrust_limit = None
            
            # 计算轨道并绘制
            self.planner.plan_orbit(
                start_year=start_year,
                start_month=start_month,
                start_day=start_day,
                tof_years=tof_years,
                departure_body=departure_body,
                arrival_body=arrival_body,
                N=N,
                rbound_factor=rbound_factor,
                thrust_limit=thrust_limit,
                plot=True
            )
            
        except Exception as e:
            messagebox.showerror("绘制错误", f"绘制过程中出现错误: {str(e)}")
    
    def calculate_porkchop(self):
        """计算猪排图数据"""
        try:
            # 获取参数
            departure_body = self.porkchop_departure_var.get()
            arrival_body = self.porkchop_arrival_var.get()
            start_year = int(self.porkchop_start_year_var.get())
            end_year = int(self.porkchop_end_year_var.get())
            tof_min = float(self.porkchop_tof_min_var.get())
            tof_max = float(self.porkchop_tof_max_var.get())
            N = int(self.porkchop_N_var.get())
            
            # 验证输入
            if start_year >= end_year:
                messagebox.showerror("输入错误", "起始年份必须小于结束年份")
                return
            
            if tof_min >= tof_max:
                messagebox.showerror("输入错误", "最小飞行时间必须小于最大飞行时间")
                return
            
            # 计算猪排图数据
            self.planner.calculate_launch_window(
                departure_body=departure_body,
                arrival_body=arrival_body,
                start_year=start_year,
                end_year=end_year,
                step_years=1,
                tof_range=(tof_min, tof_max),
                tof_step=1,
                N=N
            )
            
            messagebox.showinfo("计算完成", "猪排图数据计算完成")
            
        except Exception as e:
            messagebox.showerror("计算错误", f"计算过程中出现错误: {str(e)}")
    
    def plot_porkchop(self):
        """绘制猪排图"""
        try:
            # 绘制猪排图
            self.porkchop.plot_porkchop_contour(
                csv_path='porkchop_results.csv',
                save_path='porkchop_contour.png'
            )
            
        except Exception as e:
            messagebox.showerror("绘制错误", f"绘制过程中出现错误: {str(e)}")
    
    def optimize_direction(self):
        """优化方向"""
        try:
            # 获取参数
            start_year = int(self.dir_start_year_var.get())
            start_month = int(self.dir_start_month_var.get())
            start_day = int(self.dir_start_day_var.get())
            tof_years = float(self.dir_tof_years_var.get())
            departure_body = self.dir_departure_body_var.get()
            arrival_body = self.dir_arrival_body_var.get()
            N = int(self.dir_N_var.get())
            optimize_type = self.optimize_type_var.get()
            
            # 验证输入
            is_valid, message = self.planner.validate_input(
                start_year, start_month, start_day, tof_years, departure_body, arrival_body
            )
            if not is_valid:
                messagebox.showerror("输入错误", message)
                return
            
            # 执行优化
            if optimize_type == "出发方向":
                dep_theta, dep_phi, min_dv = self.direction_optimizer.optimize_departure_direction(
                    start_year=start_year,
                    start_month=start_month,
                    start_day=start_day,
                    tof_years=tof_years,
                    departure_body=departure_body,
                    arrival_body=arrival_body,
                    N=N
                )
                result = f"最优出发方向:\n"
                result += f"theta: {dep_theta:.4f} rad ({np.degrees(dep_theta):.2f}°)\n"
                result += f"phi: {dep_phi:.4f} rad ({np.degrees(dep_phi):.2f}°)\n"
                result += f"最小速度增量: {min_dv:.4f} km/s"
            
            elif optimize_type == "到达方向":
                arr_theta, arr_phi, min_dv = self.direction_optimizer.optimize_arrival_direction(
                    start_year=start_year,
                    start_month=start_month,
                    start_day=start_day,
                    tof_years=tof_years,
                    departure_body=departure_body,
                    arrival_body=arrival_body,
                    N=N
                )
                result = f"最优到达方向:\n"
                result += f"theta: {arr_theta:.4f} rad ({np.degrees(arr_theta):.2f}°)\n"
                result += f"phi: {arr_phi:.4f} rad ({np.degrees(arr_phi):.2f}°)\n"
                result += f"最小速度增量: {min_dv:.4f} km/s"
            
            else:  # 同时优化
                dep_theta, dep_phi, arr_theta, arr_phi, min_dv = self.direction_optimizer.optimize_both_directions(
                    start_year=start_year,
                    start_month=start_month,
                    start_day=start_day,
                    tof_years=tof_years,
                    departure_body=departure_body,
                    arrival_body=arrival_body,
                    N=N
                )
                result = f"最优出发方向:\n"
                result += f"theta: {dep_theta:.4f} rad ({np.degrees(dep_theta):.2f}°)\n"
                result += f"phi: {dep_phi:.4f} rad ({np.degrees(dep_phi):.2f}°)\n\n"
                result += f"最优到达方向:\n"
                result += f"theta: {arr_theta:.4f} rad ({np.degrees(arr_theta):.2f}°)\n"
                result += f"phi: {arr_phi:.4f} rad ({np.degrees(arr_phi):.2f}°)\n\n"
                result += f"最小速度增量: {min_dv:.4f} km/s"
            
            # 显示结果
            self.direction_result_var.set(result)
            messagebox.showinfo("优化完成", "方向优化完成")
            
        except Exception as e:
            messagebox.showerror("优化错误", f"优化过程中出现错误: {str(e)}")
    
    def plot_solar_system(self):
        """绘制太阳系"""
        try:
            # 获取参数
            year = int(self.ss_year_var.get())
            month = int(self.ss_month_var.get())
            day = int(self.ss_day_var.get())
            view_3d = self.view_type_var.get() == "3D"
            
            # 绘制太阳系
            fig, ax = self.solar_system.plot_solar_system_enhanced(year, month, day, view_3d=view_3d)
            
            # 保存并显示
            plt.savefig('solar_system.png', dpi=300, facecolor='black')
            plt.show()
            
        except Exception as e:
            messagebox.showerror("绘制错误", f"绘制过程中出现错误: {str(e)}")

if __name__ == "__main__":
    """启动桌面应用"""
    root = tk.Tk()
    app = DesktopApp(root)
    root.mainloop()
