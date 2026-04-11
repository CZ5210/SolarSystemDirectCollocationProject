import numpy as np
from scipy.optimize import minimize
from core.trajectory_optimizer import TrajectoryOptimizer
from core.solar_system import SolarSystem

class DirectionOptimizer:
    """方向优化类"""
    
    def __init__(self):
        """初始化方向优化器"""
        self.optimizer = TrajectoryOptimizer()
        self.solar_system = SolarSystem()
    
    def optimize_departure_direction(self, start_year, start_month, start_day, tof_years, 
                                   departure_body, arrival_body, N=50, rbound_factor=0.9):
        """
        优化出发方向
        
        :param start_year: 出发年份
        :param start_month: 出发月份
        :param start_day: 出发日期
        :param tof_years: 飞行时间（年）
        :param departure_body: 出发星体名称
        :param arrival_body: 到达星体名称
        :param N: 网格数（默认50）
        :param rbound_factor: 半径边界因子（默认0.9）
        :return: (optimal_theta, optimal_phi, min_dv) - 最优方向角（theta, phi）和最小速度增量
        """
        # 计算出发日期的儒略日
        start_jd = self.solar_system.date_to_julian_day(start_year, start_month, start_day)
        
        # 计算到达日期的儒略日
        tof_days = tof_years * 365.25
        end_jd = start_jd + tof_days
        
        # 获取出发和到达星体的位置和速度
        dep_pos = self.solar_system.calculate_body_position(departure_body, julian_day=start_jd)
        dep_vel = self.solar_system.calculate_body_velocity(departure_body, julian_day=start_jd)
        arr_pos = self.solar_system.calculate_body_position(arrival_body, julian_day=end_jd)
        arr_vel = self.solar_system.calculate_body_velocity(arrival_body, julian_day=end_jd)
        
        # 转换速度单位：从 AU/天 转换为 AU/年
        dep_vel = tuple(v * 365.25 for v in dep_vel)
        arr_vel = tuple(v * 365.25 for v in arr_vel)
        
        # 定义目标函数：最小化速度增量
        def objective(angles):
            theta, phi = angles
            
            # 计算出发方向单位向量
            direction = np.array([
                np.sin(theta) * np.cos(phi),
                np.sin(theta) * np.sin(phi),
                np.cos(theta)
            ])
            
            # 计算初始速度增量
            delta_v = 0.1  # 假设速度增量大小
            vx0, vy0, vz0 = dep_vel[0] + delta_v * direction[0], \
                           dep_vel[1] + delta_v * direction[1], \
                           dep_vel[2] + delta_v * direction[2]
            
            # 计算轨迹并返回速度增量
            try:
                solution = self.optimizer.trapezoidal_collocation_3d(
                    mu=4 * np.pi * np.pi,
                    x0=dep_pos[0], y0=dep_pos[1], z0=dep_pos[2],
                    vx0=vx0, vy0=vy0, vz0=vz0,
                    xf=arr_pos[0], yf=arr_pos[1], zf=arr_pos[2],
                    vxf=arr_vel[0], vyf=arr_vel[1], vzf=arr_vel[2],
                    TOF=tof_years,
                    N=N,
                    rbound=min(np.linalg.norm(dep_pos), np.linalg.norm(arr_pos)) * rbound_factor
                )
                
                # 计算速度增量
                dv = self.optimizer.visualization.calculate_DV_AUY_3d(solution, N, tof_years)
                return dv
            except Exception as e:
                return 10000  # 返回一个大值表示计算失败
        
        # 初始猜测：随机方向
        initial_guess = [np.pi/2, 0]  # 赤道方向
        
        # 优化方向角
        print("开始优化出发方向...")
        result = minimize(objective, initial_guess, method='SLSQP',
                         bounds=[(0, np.pi), (0, 2*np.pi)],
                         options={'disp': True, 'maxiter': 20})
        
        optimal_theta, optimal_phi = result.x
        min_dv = result.fun
        
        print(f"最优出发方向: theta={optimal_theta:.4f} rad, phi={optimal_phi:.4f} rad")
        print(f"最小速度增量: {min_dv:.4f} km/s")
        
        return optimal_theta, optimal_phi, min_dv
    
    def optimize_arrival_direction(self, start_year, start_month, start_day, tof_years, 
                                 departure_body, arrival_body, N=50, rbound_factor=0.9):
        """
        优化到达方向
        
        :param start_year: 出发年份
        :param start_month: 出发月份
        :param start_day: 出发日期
        :param tof_years: 飞行时间（年）
        :param departure_body: 出发星体名称
        :param arrival_body: 到达星体名称
        :param N: 网格数（默认50）
        :param rbound_factor: 半径边界因子（默认0.9）
        :return: (optimal_theta, optimal_phi, min_dv) - 最优方向角（theta, phi）和最小速度增量
        """
        # 计算出发日期的儒略日
        start_jd = self.solar_system.date_to_julian_day(start_year, start_month, start_day)
        
        # 计算到达日期的儒略日
        tof_days = tof_years * 365.25
        end_jd = start_jd + tof_days
        
        # 获取出发和到达星体的位置和速度
        dep_pos = self.solar_system.calculate_body_position(departure_body, julian_day=start_jd)
        dep_vel = self.solar_system.calculate_body_velocity(departure_body, julian_day=start_jd)
        arr_pos = self.solar_system.calculate_body_position(arrival_body, julian_day=end_jd)
        arr_vel = self.solar_system.calculate_body_velocity(arrival_body, julian_day=end_jd)
        
        # 转换速度单位：从 AU/天 转换为 AU/年
        dep_vel = tuple(v * 365.25 for v in dep_vel)
        arr_vel = tuple(v * 365.25 for v in arr_vel)
        
        # 定义目标函数：最小化速度增量
        def objective(angles):
            theta, phi = angles
            
            # 计算到达方向单位向量
            direction = np.array([
                np.sin(theta) * np.cos(phi),
                np.sin(theta) * np.sin(phi),
                np.cos(theta)
            ])
            
            # 计算终端速度增量
            delta_v = 0.1  # 假设速度增量大小
            vxf, vyf, vzf = arr_vel[0] + delta_v * direction[0], \
                           arr_vel[1] + delta_v * direction[1], \
                           arr_vel[2] + delta_v * direction[2]
            
            # 计算轨迹并返回速度增量
            try:
                solution = self.optimizer.trapezoidal_collocation_3d(
                    mu=4 * np.pi * np.pi,
                    x0=dep_pos[0], y0=dep_pos[1], z0=dep_pos[2],
                    vx0=dep_vel[0], vy0=dep_vel[1], vz0=dep_vel[2],
                    xf=arr_pos[0], yf=arr_pos[1], zf=arr_pos[2],
                    vxf=vxf, vyf=vyf, vzf=vzf,
                    TOF=tof_years,
                    N=N,
                    rbound=min(np.linalg.norm(dep_pos), np.linalg.norm(arr_pos)) * rbound_factor
                )
                
                # 计算速度增量
                dv = self.optimizer.visualization.calculate_DV_AUY_3d(solution, N, tof_years)
                return dv
            except Exception as e:
                return 10000  # 返回一个大值表示计算失败
        
        # 初始猜测：随机方向
        initial_guess = [np.pi/2, 0]  # 赤道方向
        
        # 优化方向角
        print("开始优化到达方向...")
        result = minimize(objective, initial_guess, method='SLSQP',
                         bounds=[(0, np.pi), (0, 2*np.pi)],
                         options={'disp': True, 'maxiter': 20})
        
        optimal_theta, optimal_phi = result.x
        min_dv = result.fun
        
        print(f"最优到达方向: theta={optimal_theta:.4f} rad, phi={optimal_phi:.4f} rad")
        print(f"最小速度增量: {min_dv:.4f} km/s")
        
        return optimal_theta, optimal_phi, min_dv
    
    def optimize_both_directions(self, start_year, start_month, start_day, tof_years, 
                               departure_body, arrival_body, N=50, rbound_factor=0.9):
        """
        同时优化出发和到达方向
        
        :param start_year: 出发年份
        :param start_month: 出发月份
        :param start_day: 出发日期
        :param tof_years: 飞行时间（年）
        :param departure_body: 出发星体名称
        :param arrival_body: 到达星体名称
        :param N: 网格数（默认50）
        :param rbound_factor: 半径边界因子（默认0.9）
        :return: (dep_theta, dep_phi, arr_theta, arr_phi, min_dv) - 最优方向角和最小速度增量
        """
        # 计算出发日期的儒略日
        start_jd = self.solar_system.date_to_julian_day(start_year, start_month, start_day)
        
        # 计算到达日期的儒略日
        tof_days = tof_years * 365.25
        end_jd = start_jd + tof_days
        
        # 获取出发和到达星体的位置和速度
        dep_pos = self.solar_system.calculate_body_position(departure_body, julian_day=start_jd)
        dep_vel = self.solar_system.calculate_body_velocity(departure_body, julian_day=start_jd)
        arr_pos = self.solar_system.calculate_body_position(arrival_body, julian_day=end_jd)
        arr_vel = self.solar_system.calculate_body_velocity(arrival_body, julian_day=end_jd)
        
        # 转换速度单位：从 AU/天 转换为 AU/年
        dep_vel = tuple(v * 365.25 for v in dep_vel)
        arr_vel = tuple(v * 365.25 for v in arr_vel)
        
        # 定义目标函数：最小化速度增量
        def objective(angles):
            dep_theta, dep_phi, arr_theta, arr_phi = angles
            
            # 计算出发方向单位向量
            dep_direction = np.array([
                np.sin(dep_theta) * np.cos(dep_phi),
                np.sin(dep_theta) * np.sin(dep_phi),
                np.cos(dep_theta)
            ])
            
            # 计算到达方向单位向量
            arr_direction = np.array([
                np.sin(arr_theta) * np.cos(arr_phi),
                np.sin(arr_theta) * np.sin(arr_phi),
                np.cos(arr_theta)
            ])
            
            # 计算初始和终端速度增量
            delta_v_dep = 0.1  # 假设出发速度增量大小
            delta_v_arr = 0.1  # 假设到达速度增量大小
            
            vx0, vy0, vz0 = dep_vel[0] + delta_v_dep * dep_direction[0], \
                           dep_vel[1] + delta_v_dep * dep_direction[1], \
                           dep_vel[2] + delta_v_dep * dep_direction[2]
            
            vxf, vyf, vzf = arr_vel[0] + delta_v_arr * arr_direction[0], \
                           arr_vel[1] + delta_v_arr * arr_direction[1], \
                           arr_vel[2] + delta_v_arr * arr_direction[2]
            
            # 计算轨迹并返回速度增量
            try:
                solution = self.optimizer.trapezoidal_collocation_3d(
                    mu=4 * np.pi * np.pi,
                    x0=dep_pos[0], y0=dep_pos[1], z0=dep_pos[2],
                    vx0=vx0, vy0=vy0, vz0=vz0,
                    xf=arr_pos[0], yf=arr_pos[1], zf=arr_pos[2],
                    vxf=vxf, vyf=vyf, vzf=vzf,
                    TOF=tof_years,
                    N=N,
                    rbound=min(np.linalg.norm(dep_pos), np.linalg.norm(arr_pos)) * rbound_factor
                )
                
                # 计算速度增量
                dv = self.optimizer.visualization.calculate_DV_AUY_3d(solution, N, tof_years)
                return dv
            except Exception as e:
                return 10000  # 返回一个大值表示计算失败
        
        # 初始猜测：随机方向
        initial_guess = [np.pi/2, 0, np.pi/2, 0]  # 赤道方向
        
        # 优化方向角
        print("开始同时优化出发和到达方向...")
        result = minimize(objective, initial_guess, method='SLSQP',
                         bounds=[(0, np.pi), (0, 2*np.pi), (0, np.pi), (0, 2*np.pi)],
                         options={'disp': True, 'maxiter': 30})
        
        dep_theta, dep_phi, arr_theta, arr_phi = result.x
        min_dv = result.fun
        
        print(f"最优出发方向: theta={dep_theta:.4f} rad, phi={dep_phi:.4f} rad")
        print(f"最优到达方向: theta={arr_theta:.4f} rad, phi={arr_phi:.4f} rad")
        print(f"最小速度增量: {min_dv:.4f} km/s")
        
        return dep_theta, dep_phi, arr_theta, arr_phi, min_dv

if __name__ == "__main__":
    """
    方向优化模块测试
    """
    print("===== 测试方向优化功能 =====")
    
    # 创建方向优化器实例
    optimizer = DirectionOptimizer()
    
    # 测试1：优化出发方向
    print("\n测试1：优化出发方向")
    dep_theta, dep_phi, min_dv = optimizer.optimize_departure_direction(
        start_year=2300,
        start_month=6,
        start_day=1,
        tof_years=2,
        departure_body="木星",
        arrival_body="海王星",
        N=30
    )
    print(f"最小速度增量: {min_dv:.4f} km/s")
