import numpy as np

class Constraints:
    """约束处理类"""
    
    def __init__(self):
        """初始化约束处理器"""
        pass
    
    def check_sun_distance_constraint(self, trajectory, rbound):
        """
        检查太阳距离约束
        
        :param trajectory: 轨迹状态向量
        :param rbound: 最小太阳距离约束 (AU)
        :return: (is_valid, min_distance) - 是否满足约束，最小太阳距离
        """
        # 提取位置信息
        N = len(trajectory) // 9
        x_pos = trajectory[:N]
        y_pos = trajectory[N:2*N]
        z_pos = trajectory[2*N:3*N]
        
        # 计算每个点到太阳的距离
        distances = np.sqrt(x_pos**2 + y_pos**2 + z_pos**2)
        min_distance = np.min(distances)
        
        # 检查是否满足约束
        is_valid = min_distance >= rbound
        
        return is_valid, min_distance
    
    def check_thrust_constraint(self, trajectory, thrust_limit):
        """
        检查推力约束
        
        :param trajectory: 轨迹状态向量
        :param thrust_limit: 最大推力加速度限制 (m/s²)
        :return: (is_valid, max_thrust) - 是否满足约束，最大推力
        """
        # 提取控制输入信息
        N = len(trajectory) // 9
        u_x = trajectory[6*N:7*N]
        u_y = trajectory[7*N:8*N]
        u_z = trajectory[8*N:9*N]
        
        # 计算每个点的推力大小（AU/year²）
        thrusts_au_year2 = np.sqrt(u_x**2 + u_y**2 + u_z**2)
        max_thrust_au_year2 = np.max(thrusts_au_year2)
        
        # 转换为m/s²
        # 1 AU = 149597871 km = 149597871000 m
        # 1 year = 365.25 * 24 * 3600 seconds
        meters_per_au = 149597871000
        seconds_per_year = 365.25 * 24 * 3600
        max_thrust_ms2 = max_thrust_au_year2 * meters_per_au / (seconds_per_year ** 2)
        
        # 检查是否满足约束
        is_valid = max_thrust_ms2 <= thrust_limit
        
        return is_valid, max_thrust_ms2
    
    def calculate_minimum_sun_distance(self, departure_body, arrival_body, 
                                     start_year, start_month, start_day, 
                                     tof_years):
        """
        计算轨迹可能的最小太阳距离
        
        :param departure_body: 出发星体名称
        :param arrival_body: 到达星体名称
        :param start_year: 出发年份
        :param start_month: 出发月份
        :param start_day: 出发日期
        :param tof_years: 飞行时间（年）
        :return: 最小太阳距离 (AU)
        """
        # 这里可以实现更复杂的计算，例如基于两个行星的轨道参数
        # 简单实现：使用两个行星轨道半长轴的最小值的一半
        from core.solar_system import SolarSystem
        solar_system = SolarSystem()
        
        # 获取两个行星的轨道参数
        dep_params = solar_system.bodies.get(departure_body, {})
        arr_params = solar_system.bodies.get(arrival_body, {})
        
        if not dep_params or not arr_params:
            return 0.1  # 默认最小距离
        
        # 计算两个行星的轨道半长轴
        a_dep = dep_params.get('a', 1.0)
        a_arr = arr_params.get('a', 1.0)
        
        # 估计最小太阳距离
        min_distance = min(a_dep, a_arr) * 0.5
        
        return min_distance

