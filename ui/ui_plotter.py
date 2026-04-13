import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import datetime
from core.solar_system import SolarSystem
from Param import OUTPUT_CONFIG

class UIPlotter:
    """UI绘图类，负责所有matplotlib绘图功能"""
    
    def __init__(self):
        self.fig = None
        self.canvas = None
        self.ax = None
        self.current_view = None
        self.cursors = []
        
        # 轨迹图相关属性
        self.trajectory_fig = None
        self.trajectory_canvas = None
        self.trajectory_ax = None
        self.trajectory_cursors = []
        
        # 推力图相关属性
        self.thrust_fig = None
        self.thrust_canvas = None
        self.thrust_axes = None
    
    def update_solar_system(self, viz_frame, date, solar_system):
        """更新太阳系可视化"""
        try:
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
                self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
                # 绑定鼠标事件
                self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
                self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
                self.canvas.draw()
                self.canvas.get_tk_widget().pack(fill='both', expand=True)
            else:
                # 清理旧的光标对象
                if self.cursors:
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
            _, _, self.cursors = solar_system.plot_solar_system_enhanced(
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
    
    def update_trajectory_plot(self, trajectory_frame, trajectory_data, trajectory_params):
        """更新转移轨迹图"""
        # 清除现有图形
        if self.trajectory_canvas:
            self.trajectory_canvas.get_tk_widget().destroy()
            plt.close(self.trajectory_fig)
        
        try:
            x_traj, y_traj, z_traj, ux, uy, uz, N = trajectory_data
            departure, arrival, year, month, day, tof_years = trajectory_params
            
            # 计算到达时间
            solar_system = SolarSystem()
            start_jd = solar_system.date_to_julian_day(year, month, day)
            tof_days = tof_years * 365.25
            end_jd = start_jd + tof_days
            end_year, end_month, end_day = solar_system.julian_day_to_date(end_jd)
            
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
            # 绑定鼠标事件
            self.trajectory_fig.canvas.mpl_connect('scroll_event', self.on_scroll)
            self.trajectory_fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
            
            # 绘制美化的太阳系作为背景
            _, _, self.trajectory_cursors = solar_system.plot_solar_system_enhanced(year, month, day, view_3d=True, ax=self.trajectory_ax)
            
            # 绘制轨迹
            self.trajectory_ax.plot(x_traj, y_traj, z_traj, 'b-', linewidth=2, label='转移轨迹')
            
            # 绘制推力方向（控制输入）
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
            self._update_trajectory_placeholder(trajectory_frame)
        
        # 嵌入到tkinter
        self.trajectory_canvas = FigureCanvasTkAgg(self.trajectory_fig, trajectory_frame)
        self.trajectory_canvas.draw()
        self.trajectory_canvas.get_tk_widget().pack(fill='both', expand=True)
    
    def _update_trajectory_placeholder(self, trajectory_frame):
        """更新轨迹图占位符"""
        self.trajectory_fig = plt.figure(figsize=(8, 6), facecolor='black')
        self.trajectory_fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.trajectory_ax = self.trajectory_fig.add_subplot(111, projection='3d')
        self.trajectory_ax.set_axis_off()
        self.trajectory_ax.set_box_aspect((1, 1, 1))
        self.trajectory_ax.set_title('轨迹图将在计算完成后显示', color='white')
    
    def update_trajectory_slider(self, progress, trajectory_data, trajectory_params):
        """更新轨迹时间轴滑块"""
        if not trajectory_data or not trajectory_params:
            return
        
        try:
            x_traj, y_traj, z_traj, ux, uy, uz, N = trajectory_data
            departure, arrival, year, month, day, tof_years = trajectory_params
            
            # 计算当前时间（儒略日）
            solar_system = SolarSystem()
            start_jd = solar_system.date_to_julian_day(year, month, day)
            tof_days = tof_years * 365.25
            current_jd = start_jd + progress * tof_days
            
            # 计算当前日期
            current_year, current_month, current_day = solar_system.julian_day_to_date(current_jd)
            
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
            
            # 检查是否已经有画布
            if self.trajectory_ax is not None:
                # 清除旧的内容
                if self.trajectory_cursors:
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
        except Exception as e:
            print(f"更新轨迹时间轴时出错: {e}")
    
    def update_thrust_plots(self, thrust_frame, thrust_data, trajectory_params):
        """更新推力曲线图"""
        # 清除现有图形
        if self.thrust_canvas:
            self.thrust_canvas.get_tk_widget().destroy()
            plt.close(self.thrust_fig)
        
        try:
            x, y, z, vx, vy, vz, ux, uy, uz, N = thrust_data
            departure, arrival, year, month, day, tof_years = trajectory_params
            
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
            solar_system = SolarSystem()
            distances = {}  # 存储每个星体的距离数组
            # 预先计算每个时间点的儒略日
            jds = np.zeros(N)
            for i in range(N):
                current_date = datetime.date(year, month, day) + datetime.timedelta(days=t[i])
                jds[i] = solar_system.date_to_julian_day(current_date.year, current_date.month, current_date.day)
            # 计算每个星体的距离
            for body_name in solar_system.bodies.keys():
                body_distances = np.zeros(N)
                for i in range(N):
                    # 使用儒略日计算星体位置
                    bx, by, bz = solar_system.calculate_body_position(body_name, julian_day=jds[i])
                    # 计算距离
                    body_distances[i] = np.sqrt((x[i] - bx)**2 + (y[i] - by)**2 + (z[i] - bz)**2)
                distances[body_name] = body_distances
            
            # 计算最大推力加速度
            max_thrust_accel = np.max(thrust_mag)
            
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
            for body_name in solar_system.bodies.keys():
                # 如果距离在1AU内,则不绘制
                if np.min(distances[body_name]) > 1.0:
                    continue
                # 绘制距离曲线
                color = solar_system.bodies[body_name]['color']
                ax6.plot(t, distances[body_name], color=color, linewidth=1, label=body_name)
            ax6.set_xlabel('时间 (天)', color='white')
            ax6.set_ylabel(r'距离 $AU$', color='white')
            ax6.set_ylim(0,1)
            ax6.tick_params(colors='white')
            ax6.grid(True, alpha=0.3)

            ax6.legend(loc='upper left',fontsize=8, facecolor='#2d2d2d', edgecolor='white', labelcolor='white')
            
            # 调整布局
            self.thrust_fig.tight_layout()
            
            # 嵌入到tkinter
            self.thrust_canvas = FigureCanvasTkAgg(self.thrust_fig, thrust_frame)
            self.thrust_canvas.draw()
            self.thrust_canvas.get_tk_widget().pack(fill='both', expand=True)
            
            return max_thrust_accel
            
        except Exception as e:
            print(f"更新推力曲线时出错: {e}")
            # 出错时使用占位符
            self._update_thrust_placeholder(thrust_frame)
            return 0.001
    
    def _update_thrust_placeholder(self, thrust_frame):
        """更新推力曲线占位符"""
        self.thrust_fig = plt.figure(figsize=(8, 14))
        self.thrust_fig.patch.set_facecolor('#2d2d2d')
        self.thrust_axes = self.thrust_fig.add_subplot(111)
        self.thrust_axes.set_facecolor('#2d2d2d')
        self.thrust_axes.set_title('推力曲线将在计算完成后显示', color='white')
        self.thrust_axes.tick_params(colors='white')
    
    def on_scroll(self, event):
        """鼠标滚轮缩放"""
        # 尝试获取当前活动的轴
        ax = None
        canvas = None
        
        # 检查是否是轨迹图的事件
        if self.trajectory_ax:
            # 检查事件是否来自轨迹图的画布
            if self.trajectory_canvas:
                if event.inaxes == self.trajectory_ax:
                    ax = self.trajectory_ax
                    canvas = self.trajectory_canvas
        
        # 如果不是轨迹图的事件，使用主太阳系视图的轴
        if ax is None and self.ax:
            if event.inaxes == self.ax:
                ax = self.ax
                canvas = self.canvas
        
        if ax:
            # 实现缩放逻辑
            scale_factor = 1.1
            if event.button == 'up':
                # 放大
                ax.set_xlim([x / scale_factor for x in ax.get_xlim()])
                ax.set_ylim([y / scale_factor for y in ax.get_ylim()])
                if hasattr(ax, 'set_zlim'):
                    ax.set_zlim([z / scale_factor for z in ax.get_zlim()])
            else:
                # 缩小
                ax.set_xlim([x * scale_factor for x in ax.get_xlim()])
                ax.set_ylim([y * scale_factor for y in ax.get_ylim()])
                if hasattr(ax, 'set_zlim'):
                    ax.set_zlim([z * scale_factor for z in ax.get_zlim()])
            canvas.draw()
    
    def on_motion(self, event):
        """鼠标移动事件：移除悬停注解"""
        # 当鼠标移动时，隐藏所有悬停注解
        if event.inaxes:  # 鼠标在坐标轴内
            # 清除主太阳系视图的cursor
            if self.cursors:
                for cursor in self.cursors:
                    try:
                        if cursor.selections:
                            for sel in cursor.selections:
                                if hasattr(sel, 'annotation') and sel.annotation:
                                    sel.annotation.set_visible(False)
                    except:
                        pass
            
            # 清除轨迹视图的cursor（如果有）
            if self.trajectory_cursors:
                for cursor in self.trajectory_cursors:
                    try:
                        if cursor.selections:
                            for sel in cursor.selections:
                                if hasattr(sel, 'annotation') and sel.annotation:
                                    sel.annotation.set_visible(False)
                    except:
                        pass
    
    def close_all(self):
        """关闭所有图形"""
        if self.fig:
            plt.close(self.fig)
        if self.trajectory_fig:
            plt.close(self.trajectory_fig)
        if self.thrust_fig:
            plt.close(self.thrust_fig)
