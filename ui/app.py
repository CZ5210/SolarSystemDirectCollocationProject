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
        
        # 猪排图数据属性
        self.porkchop_data = None
        self.porkchop_results = None
        
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
        
        # 猪排图轨迹滑块事件
        self.ui.porkchop_trajectory_slider.config(command=self.on_porkchop_trajectory_slider_change)
        
        # 鼠标事件
        if self.plotter.fig:
            self.plotter.fig.canvas.mpl_connect('scroll_event', self.plotter.on_scroll)
            self.plotter.fig.canvas.mpl_connect('motion_notify_event', self.plotter.on_motion)
        
        # 猪排图按钮事件
        self.ui.porkchop_button.config(command=self.calculate_porkchop)
        
        # 更新太阳系状态按钮事件
        self.ui.update_solar_button.config(command=self.update_solar_system_from_input)
    
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
            entry_date = datetime(year, month, day).date()
            # 确保current_date是日期对象
            if isinstance(self.ui.current_date, datetime):
                current_date = self.ui.current_date.date()
            else:
                # 如果是整数，假设是年份
                current_date = datetime(self.ui.current_date, 1, 1).date()
            # 计算天数差，不限制正负
            days_diff = (entry_date - current_date).days
            
            # 更新日期显示
            self.ui.date_var.set(f"{year}-{month:02d}-{day:02d}")
            
            # 只有当时间在滑块范围内（非负数）时才更新滑块
            if days_diff >= 0:
                # 检查天数差是否在滑块范围内
                current_max = self.ui.time_slider.cget('to')
                if days_diff <= current_max:
                    # 更新滑块值
                    self.ui.time_slider.set(days_diff)
                    self.ui.slider_value_var.set(f"{days_diff} 天")
                else:
                    # 对于超出滑块范围的时间，不更新滑块
                    self.ui.slider_value_var.set(f"{days_diff} 天 (超出范围)")
            else:
                # 对于过去的时间，不更新滑块
                self.ui.slider_value_var.set(f"{days_diff} 天 (过去)")
            
            # 移除自动更新太阳系状态的代码，改为由按钮触发
            
        except ValueError:
            # 输入格式错误，忽略
            pass
        except Exception as e:
            print(f"更新日期输入时出现错误: {str(e)}")
    
    def update_solar_system_from_input(self):
        """从输入的日期更新太阳系状态"""
        # 如果核心模块未就绪，不做任何操作
        if self.solar_system is None:
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
            
            # 更新太阳系状态
            self.update_solar_system(datetime(year, month, day))
            
        except ValueError:
            # 输入格式错误，忽略
            pass
        except Exception as e:
            print(f"更新太阳系状态时出现错误: {str(e)}")
    
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
    
    def calculate_porkchop(self):
        """计算猪排图"""
        # 清空日志
        self.ui.log_text.delete(1.0, tk.END)
        # 清理输出路径下的猪排图文件
        import os
        porkchop_output_dir = os.path.join("Output", "PorkChop")
        if os.path.exists(porkchop_output_dir):
            for file in os.listdir(porkchop_output_dir):
                file_path = os.path.join(porkchop_output_dir, file)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"清理文件时出错: {str(e)}")
        # 输出状态到日志
        print("正在计算猪排图...")
        self.root.update_idletasks()
        
        try:
            # 验证输入
            year = int(self.ui.year_var.get())
            month = int(self.ui.month_var.get())
            day = int(self.ui.day_var.get())
            departure = self.ui.departure_var.get()
            arrival = self.ui.arrival_var.get()
            
            # 获取猪排图参数
            try:
                min_tof = int(self.ui.min_tof_var.get())
                max_tof = int(self.ui.max_tof_var.get())
            except:
                min_tof = 180  # 默认值
                max_tof = 730  # 默认值
                
                # 更新UI
                self.ui.min_tof_var.set(str(min_tof))
                self.ui.max_tof_var.set(str(max_tof))
            
            # 获取最早和最晚出发时间
            try:
                earliest_year = int(self.ui.earliest_year_var.get())
                earliest_month = int(self.ui.earliest_month_var.get())
                earliest_day = int(self.ui.earliest_day_var.get())
                latest_year = int(self.ui.latest_year_var.get())
                latest_month = int(self.ui.latest_month_var.get())
                latest_day = int(self.ui.latest_day_var.get())
            except:
                # 默认值：今天到一年后
                from datetime import datetime
                self.current_date = datetime.now()
                earliest_year = self.current_date.year
                earliest_month = self.current_date.month
                earliest_day = self.current_date.day
                latest_year = self.current_date.year + 1
                latest_month = self.current_date.month
                latest_day = self.current_date.day
                
                # 更新UI
                self.ui.earliest_year_var.set(str(earliest_year))
                self.ui.earliest_month_var.set(str(earliest_month))
                self.ui.earliest_day_var.set(str(earliest_day))
                self.ui.latest_year_var.set(str(latest_year))
                self.ui.latest_month_var.set(str(latest_month))
                self.ui.latest_day_var.set(str(latest_day))
            
            # 最短和最长飞行时间已经从UI获取
            
            # 验证最短飞行时间
            from Param import PORKCHOP_CONFIG
            min_tof_days = PORKCHOP_CONFIG.get("min_tof_days", 20)
            if min_tof < min_tof_days:
                min_tof = min_tof_days
                print(f"最短飞行时间不能小于{min_tof_days}天，已自动调整")
            
            # 转换为年
            tof_range_years = (min_tof / 365.25, max_tof / 365.25)
            
            # 计算出发时间范围（更精确到日）
            start_year = earliest_year
            start_month = earliest_month
            start_day = earliest_day
            
            # 计算结束时间
            from datetime import datetime
            end_year = latest_year
            end_month = latest_month
            end_day = latest_day
            
            # 获取网格密度参数
            try:
                grid_density_x = int(self.ui.grid_density_x_var.get())
            except:
                grid_density_x = 3  # 默认值
            try:
                grid_density_y = int(self.ui.grid_density_y_var.get())
            except:
                grid_density_y = 3  # 默认值
            
            # 计算出发时间步长（月份）
            total_months = (end_year - start_year) * 12 + (end_month - start_month)
            step_months = max(1, total_months // (grid_density_x - 1)) if grid_density_x > 1 else 12
            
            # 导入轨道规划模块
            from features.orbit_planner import OrbitPlanner
            planner = OrbitPlanner()
            
            # 验证输入参数
            is_valid, message = planner.validate_input(
                year, month, day, 1, departure, arrival
            )
            if not is_valid:
                print(f"输入错误: {message}")
                return
            
            # 定义计算函数（用于线程执行）
            def calculate():
                try:
                    # 重定向stdout到日志文本框
                    from ui.ui_util import TextRedirector
                    with TextRedirector(self.ui.log_text, self.output_queue):
                        # 计算发射窗口
                        results_df = planner.calculate_launch_window(
                            departure_body=departure,
                            arrival_body=arrival,
                            start_year=start_year,
                            start_month=start_month,
                            start_day=start_day,
                            end_year=end_year,
                            end_month=end_month,
                            end_day=end_day,
                            step_months=step_months,
                            tof_range=tof_range_years,
                            tof_step=(max_tof - min_tof) / 365.25 / (grid_density_y - 1) if grid_density_y > 1 else 0.5,  # 根据网格密度计算步长
                            N=20  # 减小网格数加快计算
                        )
                    
                    # 计算完成后更新UI（必须在主线程中执行）
                    def update_ui():
                        # 显示结果到日志
                        print("猪排图计算完成！")
                        
                        # 保存结果
                        self.porkchop_results = results_df
                        
                        # 绘制猪排图
                        min_dv, min_dep_day, min_tof = self.plotter.plot_porkchop(self.ui.porkchop_plot_frame, results_df)
                        
                        if min_dv is not None:
                            # 更新关键数据
                            # 解析最小出发时间（天数转换为年-月-日）
                            base_year = 2026
                            base_month = 1
                            base_day = 1
                            
                            # 计算总天数
                            total_days = int(min_dep_day)
                            
                            # 转换为年-月-日
                            from datetime import datetime, timedelta
                            base_date = datetime(base_year, base_month, base_day)
                            departure_date = base_date + timedelta(days=total_days)
                            year = departure_date.year
                            month = departure_date.month
                            day = departure_date.day
                            departure_str = f"{year}-{month:02d}-{day:02d}"
                            
                            self.ui.porkchop_dv_var.set(f"ΔV: {min_dv:.4f} km/s")
                            self.ui.porkchop_tof_var.set(f"飞行时间: {min_tof:.2f} 天")
                            self.ui.porkchop_departure_var.set(f"出发时间: {departure_str}")
                            
                            # 计算到达时间
                            from core.solar_system import SolarSystem
                            solar_system = SolarSystem()
                            start_jd = solar_system.date_to_julian_day(year, month, day)
                            tof_days = min_tof
                            end_jd = start_jd + tof_days
                            end_year, end_month, end_day = solar_system.julian_day_to_date(end_jd)
                            arrival_str = f"{int(end_year)}-{int(end_month):02d}-{int(end_day):02d}"
                            self.ui.porkchop_arrival_var.set(f"到达时间: {arrival_str}")
                            
                            # 绘制太阳系可视化，显示最优轨迹
                            # 这里可以添加绘制最优轨迹的代码
                            # 暂时先绘制太阳系
                            from core.solar_system import SolarSystem
                            solar_system = SolarSystem()
                            
                            # 使用计算得到的年-月-日
                            # 这里的year, month, day已经是正确的日期值
                            # 不需要再从min_dep_year解析
                            
                            # 确保正确绘制太阳系图
                            try:
                                # 先清理可能存在的旧画布
                                if hasattr(self.plotter, 'porkchop_solar_fig'):
                                    import matplotlib.pyplot as plt
                                    plt.close(self.plotter.porkchop_solar_fig)
                                
                                # 绘制太阳系
                                self.plotter.update_solar_system(self.ui.porkchop_solar_frame, datetime(year, month, day), solar_system, is_porkchop=True)
                                # 保存引用
                                self.plotter.porkchop_solar_fig = self.plotter.porkchop_solar_fig
                                print("太阳系图绘制完成")
                                
                                # 读取并绘制所有临时弹道文件
                                import os
                                porkchop_dir = "Output/PorkChop"
                                if os.path.exists(porkchop_dir):
                                    # 遍历目录中的所有临时弹道文件
                                    for file_name in os.listdir(porkchop_dir):
                                        if file_name.startswith('temp_') and file_name.endswith('.csv'):
                                            file_path = os.path.join(porkchop_dir, file_name)
                                            try:
                                                # 读取轨迹数据
                                                solution = np.loadtxt(file_path, delimiter=',')
                                                N = 20
                                                x_traj = solution[:N]
                                                y_traj = solution[N:2*N]
                                                z_traj = solution[2*N:3*N]
                                                
                                                # 绘制轨迹（使用灰色）
                                                if self.plotter.porkchop_solar_ax is not None:
                                                    self.plotter.porkchop_solar_ax.plot(x_traj, y_traj, z_traj, 'gray', linewidth=2, alpha=0.7)
                                            except Exception as e:
                                                print(f"读取临时弹道文件 {file_name} 时出错: {e}")
                                print("临时弹道绘制完成")
                                
                                # 计算并绘制最优轨迹
                                print("正在计算最优轨迹...")
                                # 导入轨道规划模块
                                from features.orbit_planner import OrbitPlanner
                                planner = OrbitPlanner()
                                
                                # 计算最优轨迹
                                tof_years = min_tof / 365.25  # 转换为年
                                dv = planner.plan_orbit(
                                    start_year=year,
                                    start_month=month,
                                    start_day=day,  # 使用正确的日
                                    tof_years=tof_years,
                                    departure_body=departure,
                                    arrival_body=arrival,
                                    N=20,
                                    plot=False,
                                    output_dir=OUTPUT_CONFIG["directory"]
                                )
                                
                                # 生成文件名
                                file_name = f"{OUTPUT_CONFIG['directory']}/{departure}到{arrival}_{year}{month:02d}{day:02d}.csv"
                                
                                # 检查文件是否存在
                                if os.path.exists(file_name):
                                    # 读取优化结果
                                    solution = np.loadtxt(file_name, delimiter=',')
                                    
                                    # 提取轨迹数据
                                    N = 20
                                    x_traj = solution[:N]
                                    y_traj = solution[N:2*N]
                                    z_traj = solution[2*N:3*N]
                                    vx = solution[3*N:4*N]
                                    vy = solution[4*N:5*N]
                                    vz = solution[5*N:6*N]
                                    ux = solution[6*N:7*N]  # X方向推力
                                    uy = solution[7*N:8*N]  # Y方向推力
                                    uz = solution[8*N:9*N]  # Z方向推力
                                    
                                    # 保存轨迹数据
                                    trajectory_data = (x_traj, y_traj, z_traj, ux, uy, uz, N)
                                    trajectory_params = (departure, arrival, year, month, day, tof_years)
                                    
                                    # 保存猪排图轨迹数据
                                    self.porkchop_trajectory_data = trajectory_data
                                    self.porkchop_trajectory_params = trajectory_params
                                    
                                    # 保存轨迹数据，用于第二个窗口页面
                                    self.trajectory_data = trajectory_data
                                    self.trajectory_params = trajectory_params
                                    self.thrust_data = (x_traj, y_traj, z_traj, vx, vy, vz, ux, uy, uz, N)
                                    
                                    # 计算到达时间
                                    from core.solar_system import SolarSystem
                                    solar_system = SolarSystem()
                                    start_jd = solar_system.date_to_julian_day(year, month, day)
                                    tof_days = tof_years * 365.25
                                    end_jd = start_jd + tof_days
                                    end_year, end_month, end_day = solar_system.julian_day_to_date(end_jd)
                                    
                                    # 更新时间轴显示
                                    start_time = f"{year}-{month:02d}-{day:02d}"
                                    end_time = f"{int(end_year)}-{int(end_month):02d}-{int(end_day)}"
                                    self.ui.porkchop_start_time_var.set(f"出发时间: {start_time}")
                                    self.ui.porkchop_end_time_var.set(f"到达时间: {end_time}")
                                    
                                    # 更新第二个窗口页面的轨迹图和推力曲线
                                    self.plotter.update_trajectory_plot(self.ui.trajectory_frame, self.trajectory_data, self.trajectory_params)
                                    max_thrust_accel = self.plotter.update_thrust_plots(self.ui.thrust_frame, self.thrust_data, self.trajectory_params)
                                    
                                    # 更新第二个窗口页面的结果显示
                                    self.ui.update_results_display(dv, max_thrust_accel, start_time, end_time)
                                    
                                    # 在太阳系图上绘制轨迹
                                    if self.plotter.porkchop_solar_ax is not None:
                                        # 绘制轨迹
                                        self.plotter.porkchop_solar_ax.plot(x_traj, y_traj, z_traj, 'b-', linewidth=2, label='最优轨迹')
                                        
                                        # 绘制出发点和到达点
                                        self.plotter.porkchop_solar_ax.scatter([x_traj[0]], [y_traj[0]], [z_traj[0]], 
                                                             color='green', marker='o', s=50, label='出发点')
                                        self.plotter.porkchop_solar_ax.scatter([x_traj[-1]], [y_traj[-1]], [z_traj[-1]], 
                                                             color='red', marker='o', s=50, label='到达点')
                                        
                                        # 绘制推力方向（控制输入）
                                        skip = max(1, N // 20)
                                        self.plotter.porkchop_solar_ax.quiver(x_traj[::skip], y_traj[::skip], z_traj[::skip], 
                                                               ux[::skip], uy[::skip], uz[::skip], 
                                                               color='orange', length=0.1, normalize=True)
                                        
                                        # 刷新画布
                                        self.plotter.porkchop_solar_canvas.draw()
                                    
                                    print("最优轨迹绘制完成")
                                else:
                                    print(f"轨迹文件不存在: {file_name}")
                            except Exception as e:
                                print(f"绘制太阳系图和轨迹时出错: {e}")
                        
                        # 自动切换到猪排图选项卡
                        self.ui.notebook.select(2)  # 第三个选项卡（索引从0开始）
                    
                    # 在主线程中执行UI更新
                    self.root.after(0, update_ui)
                    
                except Exception as e:
                    def update_error():
                        print(f"计算猪排图时出错: {e}")
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
            print(f"计算猪排图时出错: {e}")

    def on_porkchop_trajectory_slider_change(self, value):
        """猪排图轨迹时间轴滑块变化时的回调函数"""
        if not hasattr(self, 'porkchop_trajectory_data') or not hasattr(self, 'porkchop_trajectory_params'):
            return
        
        try:
            # 获取滑块值（0-100）
            progress = float(value) / 100.0
            
            # 更新轨迹滑块
            self.update_porkchop_trajectory_slider(progress)
            
        except Exception as e:
            print(f"更新猪排图轨迹时间轴时出错: {e}")
    
    def update_porkchop_trajectory_slider(self, progress):
        """更新猪排图轨迹时间轴滑块"""
        if not hasattr(self, 'porkchop_trajectory_data') or not hasattr(self, 'porkchop_trajectory_params'):
            print("缺少轨迹数据")
            return
        
        try:
            print(f"更新猪排图轨迹时间轴，进度: {progress}")
            x_traj, y_traj, z_traj, ux, uy, uz, N = self.porkchop_trajectory_data
            departure, arrival, year, month, day, tof_years = self.porkchop_trajectory_params
            
            print(f"轨迹参数: 出发地={departure}, 目的地={arrival}, 出发时间={year}-{month}-{day}, 飞行时间={tof_years}年")
            
            # 导入SolarSystem类
            from core.solar_system import SolarSystem
            # 计算当前时间（儒略日）
            solar_system = SolarSystem()
            start_jd = solar_system.date_to_julian_day(year, month, day)
            tof_days = tof_years * 365.25
            current_jd = start_jd + progress * tof_days
            
            # 计算当前日期
            current_year, current_month, current_day = solar_system.julian_day_to_date(current_jd)
            print(f"当前日期: {current_year}-{current_month}-{current_day}")
            
            # 使用线性插值计算当前航天器位置和推力
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
            
            print(f"当前位置: ({current_x}, {current_y}, {current_z})")
            
            # 检查是否已经有画布
            if self.plotter.porkchop_solar_ax is not None:
                print("更新画布")
                # 清除旧的内容，只保留轨迹
                if hasattr(self, 'porkchop_current_markers'):
                    for marker in self.porkchop_current_markers:
                        try:
                            marker.remove()
                        except:
                            pass
                
                # 清除星体的悬停注解
                if self.plotter.porkchop_solar_cursors:
                    for cursor in self.plotter.porkchop_solar_cursors:
                        try:
                            cursor.remove()
                        except:
                            pass
                
                # 清除旧的星体标记
                if hasattr(self, 'porkchop_body_markers'):
                    for marker in self.porkchop_body_markers:
                        try:
                            marker.remove()
                        except:
                            pass
                
                # 直接更新星体位置，不清除轨迹
                print("更新星体位置")
                body_markers = []
                cursors = []
                
                # 计算并绘制每个星体
                for body_name, body in solar_system.bodies.items():
                    if body_name == "太阳":
                        continue
                    
                    try:
                        # 获取星体位置
                        x, y, z = solar_system.calculate_body_position(body_name, int(current_year), int(current_month), int(current_day))
                        
                        # 绘制星体
                        scatter = self.plotter.porkchop_solar_ax.scatter(x, y, z, color=body["color"], s=body["size"]*2, label=body_name)
                        body_markers.append(scatter)
                    except Exception as e:
                        print(f"更新星体 {body_name} 时出错: {e}")
                
                # 保存星体标记
                self.porkchop_body_markers = body_markers
                self.plotter.porkchop_solar_cursors = cursors
                
                # 绘制当前航天器位置（使用插值后的位置）
                print("绘制当前位置")
                current_pos_marker = self.plotter.porkchop_solar_ax.scatter([current_x], [current_y], [current_z], 
                                                             color='cyan', marker='*', s=100)
                
                # 绘制当前推力方向（使用插值后的推力）
                print("绘制当前推力方向")
                current_thrust_marker = self.plotter.porkchop_solar_ax.quiver([current_x], [current_y], [current_z], 
                                                           [current_ux], [current_uy], [current_uz], 
                                                           color='yellow', length=0.2, normalize=True)
                
                # 保存当前标记，以便下次更新时清除
                self.porkchop_current_markers = [current_pos_marker, current_thrust_marker]
                
                # 刷新画布
                if self.plotter.porkchop_solar_canvas:
                    print("刷新画布")
                    self.plotter.porkchop_solar_canvas.draw()
                else:
                    print("porkchop_solar_canvas 不存在")
            else:
                print("porkchop_solar_ax 不存在")
        except Exception as e:
            print(f"更新猪排图轨迹时间轴时出错: {e}")
            import traceback
            traceback.print_exc()
    
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
