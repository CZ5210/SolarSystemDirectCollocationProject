import numpy as np
import pandas as pd
import seaborn as sns
from functools import partial
from scipy.optimize import minimize
from core.visualization import Visualization
from core.solar_system import SolarSystem
import matplotlib.pyplot as plt
from matplotlib import cm, colors
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import matplotlib.patches as mpatches
from scipy.interpolate import griddata
import warnings
warnings.filterwarnings('ignore')

class TrajectoryOptimizer:
    """轨迹优化器类"""
    
    def __init__(self):
        """初始化轨迹优化器"""
        self.visualization = Visualization()
        self.solar_system = SolarSystem()
    
    def boundary_conditions_3d(self, x0, y0, z0, vx0, vy0, vz0, xf, yf, zf, vxf, vyf, vzf):
        """
        计算3D初始条件
        
        :param x0: 初始x坐标 (AU)
        :param y0: 初始y坐标 (AU)
        :param z0: 初始z坐标 (AU)
        :param vx0: 初始x速度 (AU/year)
        :param vy0: 初始y速度 (AU/year)
        :param vz0: 初始z速度 (AU/year)
        :param xf: 终点x坐标 (AU)
        :param yf: 终点y坐标 (AU)
        :param zf: 终点z坐标 (AU)
        :param vxf: 终点x速度 (AU/year)
        :param vyf: 终点y速度 (AU/year)
        :param vzf: 终点z速度 (AU/year)
        :return: (初始条件, 结束条件) - 每个条件为 [x, y, z, vx, vy, vz] 格式
        """
        
        s0 = [x0, y0, z0, vx0, vy0, vz0]
        sf = [xf, yf, zf, vxf, vyf, vzf]
        
        return s0, sf
    
    def initial_guess_line_3d(self, N, s0, sf):
        """
        生成3D线性初始猜测
        
        :param N: 网格数
        :param s0: 初始条件 [x0, y0, z0, vx0, vy0, vz0]
        :param sf: 结束条件 [xf, yf, zf, vxf, vyf, vzf]
        :return: 初始猜测状态向量
        """
        x0, y0, z0, vx0, vy0, vz0 = s0
        xf, yf, zf, vxf, vyf, vzf = sf

        states = np.zeros(9 * N)  # 3D状态变量: x, y, z, vx, vy, vz, ux, uy, uz
        for i in range(N):
            # 初始位置均匀分布
            states[i] = x0 + (xf - x0) * (i / N)
            states[N + i] = y0 + (yf - y0) * (i / N)
            states[2*N + i] = z0 + (zf - z0) * (i / N)

            # 初始速度均匀分布
            states[3*N + i] = vx0 + (vxf - vx0) * (i / N)
            states[4*N + i] = vy0 + (vyf - vy0) * (i / N)
            states[5*N + i] = vz0 + (vzf - vz0) * (i / N)

        # 控制输入初始化为零
        states[6*N:9*N] = 0.0
        return states
    
    def initial_guess_hohmann_3d(self, N, s0, sf, mu):
        """
        生成3D霍曼转移初始猜测
        
        :param N: 网格数
        :param s0: 初始条件 [x0, y0, z0, vx0, vy0, vz0]
        :param sf: 结束条件 [xf, yf, zf, vxf, vyf, vzf]
        :param mu: 引力常数 (AU^3/year^2)
        :return: 初始猜测状态向量
        """
        x0, y0, z0, vx0, vy0, vz0 = s0
        xf, yf, zf, vxf, vyf, vzf = sf

        # 计算初始和结束位置的半径
        r1 = np.sqrt(x0**2 + y0**2 + z0**2)
        r2 = np.sqrt(xf**2 + yf**2 + zf**2)
        
        # 计算霍曼转移轨道参数
        a = (r1 + r2) / 2
        e = (r2 - r1) / (r2 + r1)
        
        states = np.zeros(9 * N)  # 3D状态变量
        
        # 计算初始和结束位置的单位向量
        r1_unit = np.array([x0, y0, z0]) / r1 if r1 > 0 else np.array([1, 0, 0])
        r2_unit = np.array([xf, yf, zf]) / r2 if r2 > 0 else np.array([1, 0, 0])
        
        # 计算转移平面的法向量
        cross_product = np.cross(r1_unit, r2_unit)
        if np.linalg.norm(cross_product) > 1e-6:
            normal = cross_product / np.linalg.norm(cross_product)
        else:
            # 如果两个向量共线，使用默认法向量
            normal = np.array([0, 0, 1])
        
        # 计算第二个正交向量
        tangent = np.cross(r1_unit, normal)
        tangent /= np.linalg.norm(tangent)
        
        for i in range(N):
            theta_k = np.pi * i / (N-1)  # 真近点角从0到π
            r = a * (1 - e**2) / (1 + e * np.cos(theta_k))
            
            # 在转移平面上计算位置
            x_plane = r * np.cos(theta_k)
            y_plane = r * np.sin(theta_k)
            
            # 转换到3D空间
            states[i] = x0 + x_plane * r1_unit[0] + y_plane * tangent[0]
            states[N + i] = y0 + x_plane * r1_unit[1] + y_plane * tangent[1]
            states[2*N + i] = z0 + x_plane * r1_unit[2] + y_plane * tangent[2]
            
            # 计算椭圆轨道速度
            p = a * (1 - e**2)
            h = np.sqrt(mu * p)
            vr = (mu / h) * e * np.sin(theta_k)
            vtheta = (mu / h) * (1 + e * np.cos(theta_k))
            
            # 转换为笛卡尔速度
            vx_plane = vr * np.cos(theta_k) - vtheta * np.sin(theta_k)
            vy_plane = vr * np.sin(theta_k) + vtheta * np.cos(theta_k)
            
            states[3*N + i] = vx_plane * r1_unit[0] + vy_plane * tangent[0]
            states[4*N + i] = vx_plane * r1_unit[1] + vy_plane * tangent[1]
            states[5*N + i] = vx_plane * r1_unit[2] + vy_plane * tangent[2]
        
        # 控制输入初始化为零
        states[6*N:9*N] = 0.0
        return states
    
    def trapezoidal_collocation_3d(self, mu, x0, y0, z0, vx0, vy0, vz0, xf, yf, zf, vxf, vyf, vzf, 
                                 TOF, N, rbound=0.5, thrust_limit=None):
        """
        使用梯形配点法求解3D轨迹优化问题
        
        :param mu: 引力常数 (AU^3/year^2)
        :param x0: 初始x坐标 (AU)
        :param y0: 初始y坐标 (AU)
        :param z0: 初始z坐标 (AU)
        :param vx0: 初始x速度 (AU/year)
        :param vy0: 初始y速度 (AU/year)
        :param vz0: 初始z速度 (AU/year)
        :param xf: 终点x坐标 (AU)
        :param yf: 终点y坐标 (AU)
        :param zf: 终点z坐标 (AU)
        :param vxf: 终点x速度 (AU/year)
        :param vyf: 终点y速度 (AU/year)
        :param vzf: 终点z速度 (AU/year)
        :param TOF: 飞行时间 (年)
        :param N: 网格数
        :param rbound: 半径边界 (AU)，确保轨迹不会太靠近中心天体
        :param thrust_limit: 推力加速度限制 (m/s²)，如果为None则无限制
        :return: 优化结果状态向量
        """

        # 使用输入量的模作为目标函数
        def objective(states):
            ux = states[6*N:7*N]
            uy = states[7*N:8*N]
            uz = states[8*N:9*N]
            u = np.sqrt(ux**2 + uy**2 + uz**2)  # 控制输入的大小

            J = 0
            for k in range(N - 1):
                J += 0.5 * (u[k] ** 2 + u[k + 1] ** 2) * dt
            return J
        
        # 定义约束条件
        def equ_constraints(states, s0, sf, dt):

            # 提取状态变量
            x_pos = states[:N]
            y_pos = states[N:2*N]
            z_pos = states[2*N:3*N]
            vx = states[3*N:4*N]
            vy = states[4*N:5*N]
            vz = states[5*N:6*N]
            u_x = states[6*N:7*N]
            u_y = states[7*N:8*N]
            u_z = states[8*N:9*N]

            x0, y0, z0, vx0, vy0, vz0 = s0
            xf, yf, zf, vxf, vyf, vzf = sf

            # 计算加速度
            r = np.sqrt(x_pos**2 + y_pos**2 + z_pos**2)
            a_x = (-mu/r**3) * x_pos + u_x
            a_y = (-mu/r**3) * y_pos + u_y
            a_z = (-mu/r**3) * z_pos + u_z

            cons = []

            # 动力学约束
            for k in range(N - 1):
                cons.append(x_pos[k + 1] - x_pos[k] - 0.5 * dt * (vx[k + 1] + vx[k]))
                cons.append(y_pos[k + 1] - y_pos[k] - 0.5 * dt * (vy[k + 1] + vy[k]))
                cons.append(z_pos[k + 1] - z_pos[k] - 0.5 * dt * (vz[k + 1] + vz[k]))
                cons.append(vx[k + 1] - vx[k] - 0.5 * dt * (a_x[k + 1] + a_x[k]))
                cons.append(vy[k + 1] - vy[k] - 0.5 * dt * (a_y[k + 1] + a_y[k]))
                cons.append(vz[k + 1] - vz[k] - 0.5 * dt * (a_z[k + 1] + a_z[k]))

            # 边界约束
            cons.append(x_pos[0] - x0)
            cons.append(y_pos[0] - y0)
            cons.append(z_pos[0] - z0)
            cons.append(vx[0] - vx0)
            cons.append(vy[0] - vy0)
            cons.append(vz[0] - vz0)

            cons.append(x_pos[-1] - xf)
            cons.append(y_pos[-1] - yf)
            cons.append(z_pos[-1] - zf)
            cons.append(vx[-1] - vxf)
            cons.append(vy[-1] - vyf)
            cons.append(vz[-1] - vzf)

            return cons

        def ieq_constraints(states):
            # 提取状态变量
            x_pos = states[:N]
            y_pos = states[N:2*N]
            z_pos = states[2*N:3*N]
            u_x = states[6*N:7*N]
            u_y = states[7*N:8*N]
            u_z = states[8*N:9*N]

            # 计算约束
            r = np.sqrt(x_pos**2 + y_pos**2 + z_pos**2)
            u_mag = np.sqrt(u_x**2 + u_y**2 + u_z**2)

            cons = []
            # 半径约束
            for k in range(N):
                cons.append(r[k] - rbound)  # 半径约束
            
            # 推力约束
            if thrust_limit is not None:
                for k in range(N):
                    cons.append(thrust_limit - u_mag[k])  # 推力约束

            return cons

        # 增加优化监控函数
        def callbackF(xk):
            if not hasattr(callbackF, "iter"):
                callbackF.iter = 0  # 初始化计数器
            callbackF.iter += 1
            print(f"迭代 {callbackF.iter} 次，目标值 = {objective(xk):.6f}")
            return

        # 计算初始条件
        s0 = [x0, y0, z0, vx0, vy0, vz0]
        sf = [xf, yf, zf, vxf, vyf, vzf]

        # 计算时间步长
        dt = TOF / N

        # 设置初始猜测
        # 使用线性初始猜测
        states = self.initial_guess_line_3d(N, s0, sf)
        # 或者使用霍曼转移初始猜测
        # states = self.initial_guess_hohmann_3d(N, s0, sf, mu)

        # 定义约束条件字典
        cons1 = {'type': 'eq', 'fun': partial(equ_constraints, s0=s0, sf=sf, dt=dt)}
        cons2 = {'type': 'ineq', 'fun': ieq_constraints}

        # 求解非线性规划问题
        print("开始求解3D轨迹优化问题")

        # 使用SLSQP算法（局部优化）
        sol = minimize(objective, states, method='SLSQP', constraints=[cons1, cons2], 
                      options={'disp': True, 'maxiter': 50, 'ftol': 1e-12}, tol=1e-5, callback=callbackF)

        return sol.x
    
    def save_solution(self, solution, filename):
        """
        保存优化结果到文件
        
        :param solution: 优化结果状态向量
        :param filename: 文件名
        """
        # 保存 solution 为 CSV
        np.savetxt(filename, solution, delimiter=',')
        print(f"优化结果已保存到 {filename}")
    
    def read_solution(self, filename):
        """
        读取优化结果文件
        
        :param filename: 文件名
        :return: 优化结果状态向量
        """
        return np.loadtxt(filename, delimiter=',')
    
    def real_solar_system_trajectory(self, params):
        """
        基于真实太阳系的3D轨迹规划
        
        :param params: 参数字典，包含以下键：
            - start_year: 出发年份
            - start_month: 出发月份
            - start_day: 出发日期
            - tof_years: 飞行时间（年）
            - file_name: 保存结果的文件名
            - plot: 是否绘制结果（默认False）
            - departure_body: 出发星体名称（默认"木星"）
            - arrival_body: 到达星体名称（默认"海王星"）
            - N: 网格数（默认100）
            - mu: 太阳引力常数 (AU^3/year^2)（默认4*pi^2）
            - rbound: 最小太阳距离 (AU)（默认0.1）
            - thrust_limit: 推力加速度限制 (m/s²)（默认None）
        :return: 速度增量 (km/s)
        """
        # 从params字典中获取参数，设置默认值
        start_year = params.get('start_year', 2300)
        start_month = params.get('start_month', 6)
        start_day = params.get('start_day', 1)
        tof_years = params.get('tof_years', 2)
        file_name = params.get('file_name', 'Real_Solar_System_Trajectory.csv')
        plot = params.get('plot', False)
        departure_body = params.get('departure_body', '木星')
        arrival_body = params.get('arrival_body', '海王星')
        N = params.get('N', 20)
        mu = params.get('mu', 4 * np.pi * np.pi)  # 太阳引力常数 (AU^3/year^2)
        rbound = params.get('rbound', 0.1)  # 最小太阳距离 (AU)
        thrust_limit = params.get('thrust_limit', None)  # 推力限制
        
        # 计算出发日期的儒略日
        start_jd = self.solar_system.date_to_julian_day(start_year, start_month, start_day)
        
        # 计算到达日期的儒略日（出发日期 + 飞行时间）
        tof_days = tof_years * 365.25  # 转换为天
        end_jd = start_jd + tof_days
        
        # 计算到达日期的年月日
        end_year, end_month, end_day = self.solar_system.julian_day_to_date(end_jd)
        
        # 获取出发时刻星体的位置和速度
        print(f"\n===== 基于真实太阳系的轨迹规划 =====")
        print(f"出发日期: {start_year}-{start_month:02d}-{start_day:02d}")
        print(f"到达日期: {int(end_year)}-{int(end_month):02d}-{int(end_day):02d}")
        print(f"飞行时间: {tof_years} 年 ({tof_days:.1f} 天)")
        print(f"出发星体: {departure_body}")
        print(f"到达星体: {arrival_body}")
        
        # 计算出发星体的位置和速度
        departure_pos = self.solar_system.calculate_body_position(departure_body, julian_day=start_jd)
        departure_vel = self.solar_system.calculate_body_velocity(departure_body, julian_day=start_jd)
        x0, y0, z0 = departure_pos
        vx0, vy0, vz0 = departure_vel
        
        # 转换速度单位：从 AU/天 转换为 AU/年
        vx0 *= 365.25
        vy0 *= 365.25
        vz0 *= 365.25
        
        print(f"\n{departure_body}（出发）:")
        print(f"  位置: ({x0:.4f}, {y0:.4f}, {z0:.4f}) AU")
        print(f"  速度: ({vx0:.4f}, {vy0:.4f}, {vz0:.4f}) AU/year")
        
        # 计算到达星体的位置和速度
        arrival_pos = self.solar_system.calculate_body_position(arrival_body, julian_day=end_jd)
        arrival_vel = self.solar_system.calculate_body_velocity(arrival_body, julian_day=end_jd)
        xf, yf, zf = arrival_pos
        vxf, vyf, vzf = arrival_vel
        
        # 转换速度单位：从 AU/天 转换为 AU/年
        vxf *= 365.25
        vyf *= 365.25
        vzf *= 365.25
        
        print(f"\n{arrival_body}（到达）:")
        print(f"  位置: ({xf:.4f}, {yf:.4f}, {zf:.4f}) AU")
        print(f"  速度: ({vxf:.4f}, {vyf:.4f}, {vzf:.4f}) AU/year")
        
        # 直接使用用户指定的最小太阳距离 (AU)
        # rbound 已经在参数中设置，无需计算
        print(f"最小太阳距离约束: {rbound} AU")
        
        # 计算3D轨迹优化
        solution = self.trapezoidal_collocation_3d(
            mu, x0, y0, z0, vx0, vy0, vz0, 
            xf, yf, zf, vxf, vyf, vzf, 
            tof_years, N, rbound, thrust_limit
        )
        print("\n3D轨迹优化求解完成")
        
        # 保存优化结果
        self.save_solution(solution, file_name)
        
        # 读取优化结果
        solution = self.read_solution(file_name)
        
        # 计算速度增量
        DV = self.visualization.calculate_DV_AUY_3d(solution, N, tof_years)
        
        # 绘制结果
        if plot:
            # 准备初始和结束条件
            s0 = [x0, y0, z0, vx0, vy0, vz0]
            sf = [xf, yf, zf, vxf, vyf, vzf]
            
            # 绘制3D轨迹
            print("绘制3D轨迹...")
            # 首先绘制美化的太阳系作为背景
            fig, ax, _ = self.solar_system.plot_solar_system_enhanced(start_year, start_month, start_day, view_3d=True)
            # 然后在这个ax上绘制轨迹
            departure_time_str = f"{start_year}-{start_month:02d}-{start_day:02d}"
            arrival_time_str = f"{int(end_year)}-{int(end_month):02d}-{int(end_day):02d}"
            fig, ax = self.visualization.plot_trajectory_3d(
                s0, sf, N, solution, ax=ax, 
                dv=DV, 
                departure_time=departure_time_str, 
                arrival_time=arrival_time_str, 
                tof_years=tof_years, 
                departure_body=departure_body, 
                arrival_body=arrival_body
            )
            plt.savefig(f'{file_name}_3D_trajectory.png', dpi=300, facecolor='black')
            print(f"3D轨迹已保存为 {file_name}_3D_trajectory.png")
            
            # 绘制3D控制输入
            print("绘制3D控制输入...")
            fig = self.visualization.plot_control_3d_AUY(solution, tof_years, N)
            plt.savefig(f'{file_name}_3D_control.png', dpi=300)
            print(f"3D控制输入已保存为 {file_name}_3D_control.png")
            
            # 显示图形
            plt.show()
        
        return DV
    
    def compute_porchop_diagram(self, start_year=2300, end_year=2400, step_years=10, 
                              tof_range=(1, 10), tof_step=1, departure_body='木星', 
                              arrival_body='海王星', N=30, save_path='porchop_diagram.png'):
        """
        绘制木海转移轨迹的猪排图（Porchop Diagram）
        
        参数:
        --------
        start_year : int
            起始年份（默认2300）
        end_year : int
            结束年份（默认2400）
        step_years : int
            出发年份的步长（默认10年）
        tof_range : tuple
            飞行时间范围 (最小年数, 最大年数)（默认(1,10)）
        tof_step : float
            飞行时间步长（默认1年）
        departure_body : str
            出发星体（默认"木星"）
        arrival_body : str
            到达星体（默认"海王星"）
        N : int
            轨迹优化的网格数（默认30，减小以加快计算）
        save_path : str
            图片保存路径
        
        返回:
        --------
        pd.DataFrame: 包含出发年份、飞行时间、速度增量的数据集
        """
        # 1. 生成计算网格
        departure_years = np.arange(start_year, end_year + 1, step_years)
        tof_years_list = np.arange(tof_range[0], tof_range[1] + tof_step, tof_step)
        
        # 初始化结果数组
        dv_results = np.zeros((len(departure_years), len(tof_years_list)))
        dv_results[:] = np.nan  # 初始化为NaN，处理计算失败的情况
        
        # 2. 遍历所有出发时间和飞行时间组合计算DV
        print(f"开始计算猪排图数据 ({len(departure_years)}个出发时间 × {len(tof_years_list)}个飞行时间)")
        print("="*60)
        
        for i, dep_year in enumerate(departure_years):
            for j, tof in enumerate(tof_years_list):
                try:
                    # 构建轨迹规划参数
                    params = {
                        'start_year': dep_year,
                        'start_month': 6,       # 固定6月出发
                        'start_day': 1,         # 固定1日出发
                        'tof_years': tof,
                        'file_name': f'Output/PorkChop/temp_{dep_year}_{tof}y.csv',
                        'plot': False,
                        'departure_body': departure_body,
                        'arrival_body': arrival_body,
                        'N': N,                 # 减小网格数加快计算
                        'rbound_factor': 0.5    # 放宽边界约束
                    }
                    
                    # 计算速度增量
                    dv = self.real_solar_system_trajectory(params)
                    dv_results[i, j] = dv
                    
                    print(f"✓ 出发年份: {dep_year}, 飞行时间: {tof}年, 速度增量: {dv:.2f} km/s")
                    
                except Exception as e:
                    print(f"✗ 出发年份: {dep_year}, 飞行时间: {tof}年, 计算失败: {str(e)[:50]}")
                    dv_results[i, j] = np.nan
        
        # 3. 创建结果DataFrame
        results_df = pd.DataFrame(
            dv_results,
            index=departure_years,
            columns=[f'{tof}y' for tof in tof_years_list]
        )
        results_df.to_csv('porkchop_results.csv', float_format='%.4f')    

        return results_df

if __name__ == "__main__":
    """
    3D轨迹规划模块测试
    """
    # 创建轨迹优化器实例
    optimizer = TrajectoryOptimizer()

    # 示例1：基于真实太阳系的轨迹规划 - 木星到海王星
    print("\n===== 测试1：基于真实太阳系的轨迹规划（木星到海王星）=====")
    # 从2300年6月1日出发，飞行时间2年
    params1 = {
        'start_year': 2310,
        'start_month': 6,
        'start_day': 1,
        'tof_years': 2,
        'file_name': 'Output/Jupiter_to_Neptune_2310.csv',
        'plot': True,
        'departure_body': '木星',
        'arrival_body': '海王星',
        'rbound_factor': 0.5,  # 放宽边界约束
        'N': 50
    }
    DV1 = optimizer.real_solar_system_trajectory(params1)
    print(f"\n木星到海王星轨迹规划测试完成，速度增量：{DV1:.4f} km/s")
