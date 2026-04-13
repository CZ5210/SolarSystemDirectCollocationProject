from core.trajectory_optimizer import TrajectoryOptimizer
from core.solar_system import SolarSystem
from core.visualization import Visualization
import numpy as np
import os

class OrbitPlanner:
    """轨道规划类"""
    
    def __init__(self):
        """初始化轨道规划器"""
        self.optimizer = TrajectoryOptimizer()
        self.solar_system = SolarSystem()
        self.visualization = Visualization()
    
    def plan_orbit(self, start_year, start_month, start_day, tof_years, 
                   departure_body, arrival_body, N=20, rbound=0.1, 
                   thrust_limit=None, maxiter=50, guess_method='linear', plot=True, output_dir="Output"):
        """
        规划轨道
        
        :param start_year: 出发年份
        :param start_month: 出发月份
        :param start_day: 出发日期
        :param tof_years: 飞行时间（年）
        :param departure_body: 出发星体名称
        :param arrival_body: 到达星体名称
        :param N: 网格数（默认20）
        :param rbound: 最小太阳距离 (AU)（默认0.1）
        :param thrust_limit: 推力加速度限制 (m/s²)（默认None）
        :param plot: 是否绘制结果（默认True）
        :param output_dir: 输出目录（默认"Output"）
        :return: 速度增量 (km/s)
        """
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存原始推力限制值（m/s²）
        original_thrust_limit = thrust_limit
        
        # 单位转换：m/s² 到 AU/year²
        if thrust_limit is not None:
            # 1 AU = 149597871 km = 149597871000 m
            # 1 year = 365.25 * 24 * 3600 seconds
            au_per_m = 1 / 149597871000
            seconds_per_year = 365.25 * 24 * 3600
            thrust_limit = thrust_limit * au_per_m * (seconds_per_year ** 2)
        
        # 生成文件名
        file_name = f"{output_dir}/{departure_body}到{arrival_body}_{start_year}{start_month:02d}{start_day:02d}.csv"
        
        # 构建轨迹规划参数
        params = {
            'start_year': start_year,
            'start_month': start_month,
            'start_day': start_day,
            'tof_years': tof_years,
            'file_name': file_name,
            'plot': plot,
            'departure_body': departure_body,
            'arrival_body': arrival_body,
            'N': N,
            'rbound': rbound,
            'thrust_limit': thrust_limit,
            'maxiter': maxiter,
            'guess_method': guess_method
        }
        
        # 计算轨迹
        dv = self.optimizer.real_solar_system_trajectory(params)
        
        # 检查推力约束（使用原始m/s²值）
        if original_thrust_limit is not None:
            from features.constraints import Constraints
            constraints = Constraints()
            # 读取优化结果
            solution = np.loadtxt(file_name, delimiter=',')
            # 检查推力约束
            is_valid, max_thrust = constraints.check_thrust_constraint(solution, original_thrust_limit)
            if not is_valid:
                print(f"警告：推力约束不满足！最大推力为 {max_thrust:.6f} m/s²，超过限制 {original_thrust_limit:.6f} m/s²")
        
        # 检查太阳距离约束
        from features.constraints import Constraints
        constraints = Constraints()
        # 读取优化结果
        solution = np.loadtxt(file_name, delimiter=',')
        # 检查太阳距离约束
        is_valid, min_distance = constraints.check_sun_distance_constraint(solution, rbound)
        if not is_valid:
            print(f"警告：太阳距离约束不满足！最小距离为 {min_distance:.6f} AU，低于限制 {rbound:.6f} AU")
        
        return dv
    
    def get_planet_list(self):
        """
        获取太阳系行星列表
        
        :return: 行星名称列表
        """
        return list(self.solar_system.bodies.keys())
    
    def validate_input(self, start_year, start_month, start_day, tof_years, 
                      departure_body, arrival_body):
        """
        验证输入参数
        
        :param start_year: 出发年份
        :param start_month: 出发月份
        :param start_day: 出发日期
        :param tof_years: 飞行时间（年）
        :param departure_body: 出发星体名称
        :param arrival_body: 到达星体名称
        :return: (is_valid, message)
        """
        # 验证年份
        if start_year < 1900:
            return False, "出发年份必须在1900以后"
        
        # 验证月份
        if start_month < 1 or start_month > 12:
            return False, "月份必须在1-12之间"
        
        # 验证日期
        if start_day < 1 or start_day > 31:
            return False, "日期必须在1-31之间"
        
        # 验证飞行时间
        if tof_years*365.25 < 10 or tof_years > 20:
            return False, "飞行时间必须在10天-20年之间"
        
        # 验证月份是否正确（闰年，2月31这种问题）
        # 每月的天数
        days_in_month = {
            1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
            7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31
        }
        
        # 检查闰年
        is_leap_year = (start_year % 4 == 0 and start_year % 100 != 0) or (start_year % 400 == 0)
        if is_leap_year:
            days_in_month[2] = 29
        
        # 验证日期是否在当月的有效范围内
        if start_day > days_in_month[start_month]:
            return False, f"{start_year}年{start_month}月只有{days_in_month[start_month]}天"

        # 验证星体名称
        planet_list = self.get_planet_list()
        if departure_body not in planet_list:
            return False, f"出发星体必须是以下之一: {', '.join(planet_list)}"
        
        if arrival_body not in planet_list:
            return False, f"到达星体必须是以下之一: {', '.join(planet_list)}"
        
        return True, "输入参数有效"
    
    def calculate_launch_window(self, departure_body, arrival_body, 
                               start_year, end_year, step_years=1, 
                               tof_range=(1, 10), tof_step=1, N=30):
        """
        计算发射窗口
        
        :param departure_body: 出发星体名称
        :param arrival_body: 到达星体名称
        :param start_year: 起始年份
        :param end_year: 结束年份
        :param step_years: 年份步长（默认1）
        :param tof_range: 飞行时间范围（默认(1, 10)）
        :param tof_step: 飞行时间步长（默认1）
        :param N: 网格数（默认30）
        :return: 猪排图数据
        """
        # 确保Output/PorkChop目录存在
        porkchop_dir = "Output/PorkChop"
        if not os.path.exists(porkchop_dir):
            os.makedirs(porkchop_dir)
        
        # 计算猪排图
        results_df = self.optimizer.compute_porchop_diagram(
            start_year=start_year,
            end_year=end_year,
            step_years=step_years,
            tof_range=tof_range,
            tof_step=tof_step,
            departure_body=departure_body,
            arrival_body=arrival_body,
            N=N
        )
        
        return results_df

if __name__ == "__main__":
    """
    轨道规划模块测试
    """
    print("===== 测试轨道规划功能 =====")
    
    # 创建轨道规划器实例
    planner = OrbitPlanner()
    
    # 测试1：木星到海王星轨道规划
    print("\n测试1：木星到海王星轨道规划")
    dv = planner.plan_orbit(
        start_year=2300,
        start_month=6,
        start_day=1,
        tof_years=2,
        departure_body="木星",
        arrival_body="海王星",
        N=50,
        rbound_factor=0.5,
        plot=True
    )
    print(f"速度增量: {dv:.4f} km/s")
    
    # 测试2：获取行星列表
    print("\n测试2：获取行星列表")
    planets = planner.get_planet_list()
    print(f"太阳系行星: {', '.join(planets)}")
    
    # 测试3：验证输入参数
    print("\n测试3：验证输入参数")
    is_valid, message = planner.validate_input(
        start_year=2300,
        start_month=6,
        start_day=1,
        tof_years=2,
        departure_body="木星",
        arrival_body="海王星"
    )
    print(f"输入验证: {is_valid}, {message}")
