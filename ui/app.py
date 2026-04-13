import warnings
warnings.filterwarnings("ignore", message="3d coordinates not supported yet", category=UserWarning)

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from datetime import datetime
import sys
import os
import threading
import queue

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入参数配置
from Param import TIME_CONFIG, OUTPUT_CONFIG

# 导入自定义模块
from ui.ui_util import TextRedirector, clean_output_directory
from ui.ui_component import UIComponent
from ui.ui_plotter import UIPlotter

class App:
    """主应用类，整合所有UI组件和功能"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("太阳系轨道设计工具")
        self.root.geometry("1600x1400")
        self.root.configure(bg="#2d2d2d")
        
        # 初始化属性
        self.solar_system = None
        self._updating_from_slider = False  # 用于避免循环更新
        self.output_queue = queue.Queue()  # 用于线程间通信的队列
        
        # 轨迹数据属性
        self.trajectory_data = None
        self.trajectory_params = None
        self.thrust_data = None
        
        # 初始化UI组件
        self.ui = UIComponent(self.root)
        self.ui.create_ui()
        
        # 初始化绘图工具
        self.plotter = UIPlotter()
        
        # 清理输出目录
        clean_output_directory()
        
        # 设置窗口关闭时的资源清理回调
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 启动输出队列处理
        self.root.after(100, self.process_queue)
        
        # 绑定事件处理
        self._bind_events()
        
        # 尝试加载核心模块
        self._init_core_module()
    
    def _bind_events(self):
        """绑定事件处理"""
        # 时间滑块事件
        self.ui.time_slider.config(command=self.update_date)
        
        # 日期输入框事件
        self.ui.year_var.trace_add("write", self.on_date_entry_change)
        self.ui.month_var.trace_add("write", self.on_date_entry_change)
        self.ui.day_var.trace_add("write", self.on_date_entry_change)
        
        # 计算按钮事件
        self.ui.calculate_button.config(command=self.calculate_trajectory)
        
        # 日志折叠按钮事件
        self.ui.log_toggle_button.config(command=self.ui.toggle_log)
        
        # 轨迹滑块事件
        self.ui.trajectory_slider.config(command=self.on_trajectory_slider_change)
        
        # 鼠标事件
        if self.plotter.fig:
            self.plotter.fig.canvas.mpl_connect('scroll_event', self.plotter.on_scroll)
            self.plotter.fig.canvas.mpl_connect('motion_notify_event', self.plotter.on_motion)
    
    def process_queue(self):
        """处理输出队列，实时更新日志文本框"""
        try:
            while True:
                string = self.output_queue.get_nowait()
                self.ui.log_text.insert(tk.END, string)
                self.ui.log_text.see(tk.END)
                self.root.update_idletasks()
        except queue.Empty:
            pass
        finally:
            # 每隔100毫秒检查一次队列
            self.root.after(100, self.process_queue)
    
    def _init_core_module(self):
        """尝试导入并初始化 SolarSystem 模块"""
        try:
            from core.solar_system import SolarSystem
            self.solar_system = SolarSystem()
            # 初始化成功，进行首次绘图
            self.update_solar_system()
            
            # 获取行星列表（排除太阳）
            planet_list = [name for name in self.solar_system.bodies.keys() if name != "太阳"]
            self.ui.set_planet_list(planet_list)
            
        except Exception as e:
            # 显示错误并禁用时间滑块，但窗口仍然可以正常关闭
            messagebox.showerror("初始化错误", 
                f"无法加载太阳系模块：{str(e)}\n\n程序将无法显示太阳系可视化，但窗口可以正常关闭。")
            self.ui.time_slider.config(state=tk.DISABLED)
            # 禁用轨迹规划控件
            self.ui.disable_trajectory_controls()
            # 在可视化框架中显示错误信息
            error_label = ttk.Label(self.ui.viz_frame, text=f"核心模块加载失败:\n{str(e)}", 
                                    style="Dark.TLabel", font=('Arial', 12))
            error_label.pack(expand=True)
    
    def update_date(self, value):
        """滑块回调：更新日期和可视化"""
        # 如果核心模块未就绪，不做任何操作
        if self.solar_system is None:
            return
        
        try:
            days = int(float(value))
            # 确保时间只能前进，不能后退
            current_days = int(self.ui.time_slider.get())
            if days < current_days:
                # 如果尝试后退，保持当前值
                self.ui.time_slider.set(current_days)
                return
            
            adjusted_date = self.ui.current_date.replace(hour=0, minute=0, second=0, microsecond=0)
            adjusted_date = adjusted_date.fromordinal(adjusted_date.toordinal() + days)
            
            # 更新界面控件（它们一定存在，因为 UI 已先创建）
            # 暂时禁用回调，避免循环更新
            self._updating_from_slider = True
            try:
                self.ui.update_date_display(adjusted_date, days)
            finally:
                self._updating_from_slider = False
            
            # 更新可视化
            self.update_solar_system(adjusted_date)
        except Exception as e:
            print(f"更新日期时出现错误: {str(e)}")
    
    def update_solar_system(self, date=None):
        """更新太阳系可视化"""
        if self.solar_system is None:
            return
        
        if date is None:
            date = self.ui.current_date
        
        self.plotter.update_solar_system(self.ui.viz_frame, date, self.solar_system)
    
    def on_date_entry_change(self, *args):
        """出发时间输入框变化时的回调函数"""
        # 如果核心模块未就绪，不做任何操作
        if self.solar_system is None:
            return
        
        # 如果是从滑块更新触发的，避免循环更新
        if self._updating_from_slider:
            return
        
        try:
            # 获取输入的日期
            year = int(self.ui.year_var.get())
            month = int(self.ui.month_var.get())
            day = int(self.ui.day_var.get())
            
            # 验证日期有效性
            from features.orbit_planner import OrbitPlanner
            planner = OrbitPlanner()
            is_valid, message = planner.validate_input(year, month, day, 1, "地球", "火星")
            if not is_valid:
                return
            
            # 计算与当前日期的天数差
            import datetime
            entry_date = datetime.date(year, month, day)
            current_date = self.ui.current_date.date()
            days_diff = (entry_date - current_date).days
            
            # 更新日期显示
            self.ui.date_var.set(f"{year}-{month:02d}-{day:02d}")
            
            # 只有当时间在滑块范围内（非负数）时才更新滑块
            if days_diff >= 0:
                self.ui.time_slider.set(days_diff)
                self.ui.slider_value_var.set(f"{days_diff} 天")
            else:
                # 对于过去的时间，不更新滑块，但仍然更新可视化
                self.ui.slider_value_var.set(f"{days_diff} 天 (过去)")
            
            # 更新可视化（无论时间是否在滑块范围内）
            self.update_solar_system(datetime.datetime(year, month, day))
            
        except ValueError:
            # 输入格式错误，忽略
            pass
        except Exception as e:
            print(f"更新日期输入时出现错误: {str(e)}")
    
    def calculate_trajectory(self):
        """计算轨迹按钮回调函数"""
        # 清空日志
        self.ui.log_text.delete(1.0, tk.END)
        # 输出状态到日志
        print("正在计算...")
        self.root.update_idletasks()
        
        try:
            # 验证输入
            year = int(self.ui.year_var.get())
            month = int(self.ui.month_var.get())
            day = int(self.ui.day_var.get())
            # 支持数学表达式计算
            tof_days_str = self.ui.tof_days_var.get().strip()
            try:
                tof_days = float(eval(tof_days_str))
            except:
                tof_days = 365  # 默认值
            departure = self.ui.departure_var.get()
            arrival = self.ui.arrival_var.get()
            N = int(self.ui.N_var.get())
            rbound = float(self.ui.rbound_var.get())
            thrust_str = self.ui.thrust_var.get().strip()
            thrust_limit = float(thrust_str) if thrust_str else None
            maxiter = int(self.ui.maxiter_var.get())
            guess_method = self.ui.guess_method_var.get()
            
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
                    with TextRedirector(self.ui.log_text, self.output_queue):
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
                        
                        # 生成文件名（与plan_orbit方法一致）
                        file_name = f"{OUTPUT_CONFIG['directory']}/{departure}到{arrival}_{year}{month:02d}{day:02d}.csv"
                        
                        # 检查文件是否存在
                        if os.path.exists(file_name):
                            # 读取优化结果
                            solution = np.loadtxt(file_name, delimiter=',')
                            
                            # 提取轨迹数据
                            x_traj = solution[:N]
                            y_traj = solution[N:2*N]
                            z_traj = solution[2*N:3*N]
                            vx = solution[3*N:4*N]
                            vy = solution[4*N:5*N]
                            vz = solution[5*N:6*N]
                            ux = solution[6*N:7*N]  # X方向推力
                            uy = solution[7*N:8*N]  # Y方向推力
                            uz = solution[8*N:9*N]  # Z方向推力
                            
                            # 保存轨迹数据，用于时间轴滑块
                            self.trajectory_data = (x_traj, y_traj, z_traj, ux, uy, uz, N)
                            self.trajectory_params = (departure, arrival, year, month, day, tof_years)
                            self.thrust_data = (x_traj, y_traj, z_traj, vx, vy, vz, ux, uy, uz, N)
                            
                            # 计算到达时间
                            from core.solar_system import SolarSystem
                            solar_system = SolarSystem()
                            start_jd = solar_system.date_to_julian_day(year, month, day)
                            tof_days = tof_years * 365.25
                            end_jd = start_jd + tof_days
                            end_year, end_month, end_day = solar_system.julian_day_to_date(end_jd)
                            
                            # 更新轨迹图和推力曲线
                            self.plotter.update_trajectory_plot(self.ui.trajectory_frame, self.trajectory_data, self.trajectory_params)
                            max_thrust_accel = self.plotter.update_thrust_plots(self.ui.thrust_frame, self.thrust_data, self.trajectory_params)
                            
                            # 更新结果显示
                            start_time = f"{year}-{month:02d}-{day:02d}"
                            end_time = f"{int(end_year)}-{int(end_month):02d}-{int(end_day):02d}"
                            self.ui.update_results_display(dv, max_thrust_accel, start_time, end_time)
                            
                            # 自动切换到结果选项卡
                            self.ui.notebook.select(1)  # 第二个选项卡（索引从0开始）
                    
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
    
    def on_trajectory_slider_change(self, value):
        """轨迹时间轴滑块变化时的回调函数"""
        if self.trajectory_data is None:
            return
        
        try:
            # 获取滑块值（0-100）
            progress = float(value) / 100.0
            
            # 更新轨迹滑块
            self.plotter.update_trajectory_slider(progress, self.trajectory_data, self.trajectory_params)
            
        except Exception as e:
            print(f"更新轨迹时间轴时出错: {e}")
    
    def on_closing(self):
        """窗口关闭时清理 Matplotlib 资源并退出"""
        try:
            # 关闭所有 matplotlib 图形
            self.plotter.close_all()
            # 销毁主窗口
            self.root.destroy()
        except Exception as e:
            print(f"清理资源时出错: {e}")
        finally:
            # 确保进程退出（解决某些环境下的残留问题）
            sys.exit(0)
