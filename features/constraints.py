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
        :param thrust_limit: 最大推力加速度限制 (AU/year²)
        :return: (is_valid, max_thrust) - 是否满足约束，最大推力
        """
        # 提取控制输入信息
        N = len(trajectory) // 9
        u_x = trajectory[6*N:7*N]
        u_y = trajectory[7*N:8*N]
        u_z = trajectory[8*N:9*N]
        
        # 计算每个点的推力大小
        thrusts = np.sqrt(u_x**2 + u_y**2 + u_z**2)
        max_thrust = np.max(thrusts)
        
        # 检查是否满足约束
        is_valid = max_thrust <= thrust_limit
        
        return is_valid, max_thrust
    
    def convert_thrust_units(self, thrust, from_unit, to_unit):
        """
        转换推力单位
        
        :param thrust: 推力值
        :param from_unit: 源单位 ('km/s²', 'AU/year²')
        :param to_unit: 目标单位 ('km/s²', 'AU/year²')
        :return: 转换后的推力值
        """
        if from_unit == to_unit:
            return thrust
        
        # 转换因子: 1 AU/year² = (149597871 km) / (365.25*24*3600 s)^2
        conversion_factor = 149597871 / ((365.25 * 24 * 3600) ** 2)
        
        if from_unit == 'AU/year²' and to_unit == 'km/s²':
            return thrust * conversion_factor
        elif from_unit == 'km/s²' and to_unit == 'AU/year²':
            return thrust / conversion_factor
        else:
            raise ValueError(f"不支持的单位转换: {from_unit} -> {to_unit}")
    
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

if __name__ == "__main__":
    """
    约束处理模块测试
    """
    print("===== 测试约束处理功能 =====")
    
    # 创建约束处理器实例
    constraints = Constraints()
    
    # 测试1：单位转换
    print("\n测试1：单位转换")
    thrust_au_year2 = 1.0
    thrust_km_s2 = constraints.convert_thrust_units(thrust_au_year2, 'AU/year²', 'km/s²')
    print(f"1 AU/year² = {thrust_km_s2:.6f} km/s²")
    
    # 测试2：最小太阳距离计算
    print("\n测试2：最小太阳距离计算")
    min_distance = constraints.calculate_minimum_sun_distance(
        departure_body="木星",
        arrival_body="海王星",
        start_year=2300,
        start_month=6,
        start_day=1,
        tof_years=2
    )
    print(f"最小太阳距离估计: {min_distance:.4f} AU")
