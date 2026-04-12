import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

# 设置支持中文的字体 
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class Visualization:
    """可视化引擎类"""
    
    def __init__(self):
        """初始化可视化引擎"""
        pass
    
    def read_solution(self, filename):
        """
        读取保存的优化结果
        
        :param filename: 文件名
        :return: 优化结果状态向量
        """
        solution = np.loadtxt(filename, delimiter=',')
        return solution
    
    def plot_trajectory_3d(self, s0, sf, N, solution, size=10, ax=None, dv=None, 
                          departure_time=None, arrival_time=None, tof_years=None, 
                          departure_body=None, arrival_body=None):
        """
        绘制3D轨迹
        
        :param s0: 初始条件 [x0, y0, z0, vx0, vy0, vz0]
        :param sf: 结束条件 [xf, yf, zf, vxf, vyf, vzf]
        :param r1: 初始轨道半径 (AU)
        :param r2: 结束轨道半径 (AU)
        :param N: 网格数
        :param solution: 优化结果状态向量
        :param size: 速度向量和控制输入向量的大小缩放因子
        :param ax: 可选的3D轴对象，如果提供了ax，就使用它，否则创建一个新的ax
        :param dv: 速度增量 (km/s)
        :param departure_time: 出发时间 (字符串)
        :param arrival_time: 到达时间 (字符串)
        :param tof_years: 飞行时间 (年)
        :param departure_body: 出发星体名称
        :param arrival_body: 到达星体名称
        :return: (fig, ax) - 3D图形对象和轴对象
        """
        x0, y0, z0, vx0, vy0, vz0 = s0
        xf, yf, zf, vxf, vyf, vzf = sf

        # 如果没有提供ax，创建3D图形
        if ax is None:
            fig = plt.figure(figsize=(14, 12))
            ax = fig.add_subplot(111, projection='3d')
        else:
            fig = ax.get_figure()

        # 绘制出发点和速度向量
        ax.scatter(x0, y0, z0, color='green', marker='o', facecolors='none', s=50, label='出发点')
        ax.quiver(x0, y0, z0, vx0, vy0, vz0, color='green', length=size/10, normalize=True)

        # 绘制目标点和速度向量
        ax.scatter(xf, yf, zf, color='blue', marker='o', facecolors='none', s=50, label='目标点')
        ax.quiver(xf, yf, zf, vxf, vyf, vzf, color='blue', length=size/10, normalize=True)

        # 绘制轨迹
        x_traj = solution[:N]
        y_traj = solution[N:2*N]
        z_traj = solution[2*N:3*N]
        ax.plot(x_traj, y_traj, z_traj, color='red', label='飞行弹道')

        # 绘制控制输入向量
        ux = solution[6*N:7*N]
        uy = solution[7*N:8*N]
        uz = solution[8*N:9*N]
        ax.quiver(x_traj, y_traj, z_traj, ux, uy, uz, color='orange', length=size/100, normalize=True, label='控制输入')

        # 设置坐标轴标签
        ax.set_xlabel('X轴 (AU)')
        ax.set_ylabel('Y轴 (AU)')
        ax.set_zlabel('Z轴 (AU)')

        # 设置标题
        if departure_body and arrival_body:
            ax.set_title(f'{departure_body}到{arrival_body}的3D轨迹可视化')
        else:
            ax.set_title('3D轨迹可视化')

        # 添加图例
        ax.legend(loc='upper left')

        # 设置坐标轴范围相等
        max_range = max(np.max(np.abs(x_traj)), np.max(np.abs(y_traj)), np.max(np.abs(z_traj)))
        ax.set_xlim([-max_range, max_range])
        ax.set_ylim([-max_range, max_range])
        ax.set_zlim([-max_range, max_range])

        ax.set_aspect('equal')

        # 添加文本标注
        if dv is not None or departure_time is not None or tof_years is not None:
            # 计算标注位置（在图形的右上角）
            text_x = max_range * 0.8
            text_y = max_range * 0.8
            text_z = max_range * 0.8
            
            # 构建标注文本
            annotation_text = "轨迹信息:\n"
            if departure_body and arrival_body:
                annotation_text += f"出发星体: {departure_body}\n"
                annotation_text += f"到达星体: {arrival_body}\n"
            if departure_time:
                annotation_text += f"出发时间: {departure_time}\n"
            if arrival_time:
                annotation_text += f"到达时间: {arrival_time}\n"
            if tof_years is not None:
                annotation_text += f"飞行时间: {tof_years:.2f} 年\n"
            if dv is not None:
                annotation_text += f"速度增量: {dv:.4f} km/s"
            
            # 添加文本标注
            ax.text(text_x, text_y, text_z, annotation_text, color='white', fontsize=10, bbox=dict(facecolor='black', alpha=0.7))

        return fig, ax
    
    def plot_control_3d(self, solution, TOF, N):
        """
        绘制3D控制输入
        
        :param solution: 优化结果状态向量
        :param TOF: 飞行时间 (年)
        :param N: 网格数
        :return: (fig, fig2) - 控制输入分量和模的图形对象
        """
        u_x = solution[6*N:7*N]
        u_y = solution[7*N:8*N]
        u_z = solution[8*N:9*N]

        t = np.linspace(0, TOF, N)
        
        # 创建三个子图
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8))
        
        # 绘制x方向控制输入
        ax1.plot(t, u_x, label='u_x', color='r')
        ax1.set_xlabel('时间(年)')
        ax1.set_ylabel('控制输入 (AU/year²)')
        ax1.set_title('x方向控制输入')
        ax1.grid()
        ax1.legend()
        
        # 绘制y方向控制输入
        ax2.plot(t, u_y, label='u_y', color='g')
        ax2.set_xlabel('时间(年)')
        ax2.set_ylabel('控制输入 (AU/year²)')
        ax2.set_title('y方向控制输入')
        ax2.grid()
        ax2.legend()
        
        # 绘制z方向控制输入
        ax3.plot(t, u_z, label='u_z', color='b')
        ax3.set_xlabel('时间(年)')
        ax3.set_ylabel('控制输入 (AU/year²)')
        ax3.set_title('z方向控制输入')
        ax3.grid()
        ax3.legend()
        
        plt.tight_layout()
        
        # 绘制控制输入模
        fig2, ax4 = plt.subplots(figsize=(10, 4))
        u_mag = np.sqrt(u_x**2 + u_y**2 + u_z**2)
        ax4.plot(t, u_mag, label='控制输入模', color='purple')
        ax4.set_xlabel('时间(年)')
        ax4.set_ylabel('控制输入模 (AU/year²)')
        ax4.set_title('3D控制输入模时间历史')
        ax4.grid()
        ax4.legend()
        
        plt.tight_layout()
        
        return fig, fig2
    
    def plot_control_3d_AUY(self, solution, TOF, N):
        """
        绘制3D控制输入（转换为km/s²）
        
        :param solution: 优化结果状态向量
        :param TOF: 飞行时间 (年)
        :param N: 网格数
        :return: fig - 包含所有子图的图形对象
        """
        u_x = solution[6*N:7*N]
        u_y = solution[7*N:8*N]
        u_z = solution[8*N:9*N]

        # 将加速度从AU/year^2转换为m/s^2
        u_x = u_x * (149597871 / ((365*24*3600)**2))*1000
        u_y = u_y * (149597871 / ((365*24*3600)**2))*1000
        u_z = u_z * (149597871 / ((365*24*3600)**2))*1000

        t = np.linspace(0, TOF, N)
        # 将时间从年转化为月
        t = t * 12  # 转换为月
        
        # 创建一个包含四个子图的图形
        fig = plt.figure(figsize=(12, 10))
        
        # 绘制x方向控制输入
        ax1 = fig.add_subplot(411)
        ax1.plot(t, u_x, label='u_x', color='r')
        ax1.set_ylabel(r'控制输入 ($m/s^2$)')
        ax1.set_title('x方向控制输入')
        ax1.grid()
        ax1.legend()
        
        # 绘制y方向控制输入
        ax2 = fig.add_subplot(412)
        ax2.plot(t, u_y, label='u_y', color='g')
        ax2.set_ylabel(r'控制输入 ($m/s^2$)')
        ax2.set_title('y方向控制输入')
        ax2.grid()
        ax2.legend()
        
        # 绘制z方向控制输入
        ax3 = fig.add_subplot(413)
        ax3.plot(t, u_z, label='u_z', color='b')
        ax3.set_ylabel(r'控制输入 ($m/s^2$)')
        ax3.set_title('z方向控制输入')
        ax3.grid()
        ax3.legend()
        
        # 绘制控制输入模
        ax4 = fig.add_subplot(414)
        u_mag = np.sqrt(u_x**2 + u_y**2 + u_z**2)
        ax4.plot(t, u_mag, label='控制输入模', color='purple')
        ax4.set_xlabel('时间(月)')
        ax4.set_ylabel(r'控制输入模 ($m/s^2$)')
        ax4.set_title('3D控制输入模时间历史')
        ax4.grid()
        ax4.legend()
        
        plt.tight_layout()
        
        return fig
    
    def calculate_DV_AUY_3d(self, solution, N, TOF):
        """
        计算3D控制输入的速度增量
        
        :param solution: 优化结果状态向量
        :param N: 网格数
        :param TOF: 飞行时间 (年)
        :return: 速度增量 (km/s)
        """
        u_x = solution[6*N:7*N]
        u_y = solution[7*N:8*N]
        u_z = solution[8*N:9*N]

        # 将加速度从AU/year^2转换为km/s^2
        u_x = u_x * (149597871 / ((365*24*3600)**2))
        u_y = u_y * (149597871 / ((365*24*3600)**2))
        u_z = u_z * (149597871 / ((365*24*3600)**2))

        dt = TOF / N  # 时间步长
        
        # 将时间从年转化为s以正确积分
        dt = dt * 365 * 24 * 3600  # 转换为秒

        # 计算控制输入的模
        u = np.sqrt(u_x**2 + u_y**2 + u_z**2)

        # 将加速度的模转换为速度增量DV
        DV = np.trapezoid(u, dx=dt)  # 使用梯形积分

        print("3D速度增量：", DV.round(4), ' km/s')

        return DV

if __name__ == "__main__":
    """
    3D轨迹可视化模块测试
    """
    print("===== 测试3D轨迹可视化功能 =====")
    print("此模块提供3D轨迹绘制、控制输入绘制和速度增量计算功能")
    print("请在trajectory_optimizer.py中调用这些函数进行测试")
