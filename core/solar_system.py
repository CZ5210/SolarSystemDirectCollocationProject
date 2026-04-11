
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import mplcursors

# 设置支持中文的字体 
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class SolarSystem:
    """太阳系模型类"""
    
    def __init__(self):
        """初始化太阳系模型"""
        # 太阳系主要星体的轨道参数（基于J2000历元，单位：AU, 度）
        self.bodies = {
            "太阳": {
                "a": 0.0,
                "e": 0.0,
                "i": 0.0,
                "Omega": 0.0,
                "omega": 0.0,
                "M0": 0.0,
                "n": 0.0,
                "color": "orange",
                "size": 30,
                "radius": 696340 / 149597870.7  # 太阳半径（AU）
            },
            "水星": {
                "a": 0.38709893,
                "e": 0.20563069,
                "i": 7.00487,
                "Omega": 48.33167,
                "omega": 77.45645,
                "M0": 252.25084,
                "n": 4.0923344368,
                "color": "gray",
                "size": 2,
                "radius": 2440 / 149597870.7
            },
            "金星": {
                "a": 0.72333199,
                "e": 0.00677323,
                "i": 3.39471,
                "Omega": 76.68069,
                "omega": 131.53298,
                "M0": 181.97973,
                "n": 1.6021302244,
                "color": "yellow",
                "size": 2,
                "radius": 6052 / 149597870.7
            },
            "地球": {
                "a": 1.00000011,
                "e": 0.01671022,
                "i": 0.00005,
                "Omega": -11.26064,
                "omega": 102.94719,
                "M0": 356.0470,
                "n": 0.98560926,
                "color": "blue",
                "size": 2,
                "radius": 6371 / 149597870.7
            },
            "火星": {
                "a": 1.52366231,
                "e": 0.09341233,
                "i": 1.85061,
                "Omega": 49.57854,
                "omega": 336.04084,
                "M0": 19.412,
                "n": 0.52403840,
                "color": "red",
                "size": 2,
                "radius": 3390 / 149597870.7
            },
            "木星": {
                "a": 5.20436301,
                "e": 0.04839266,
                "i": 1.30530,
                "Omega": 100.55615,
                "omega": 14.75385,
                "M0": 20.020,
                "n": 0.08308530,
                "color": "brown",
                "size": 10,
                "radius": 69911 / 149597870.7
            },
            "土星": {
                "a": 9.53707032,
                "e": 0.05316192,
                "i": 2.48446,
                "Omega": 113.71504,
                "omega": 92.43194,
                "M0": 317.020,
                "n": 0.03344422,
                "color": "gold",
                "size": 10,
                "radius": 58232 / 149597870.7
            },
            "天王星": {
                "a": 19.19126393,
                "e": 0.04756877,
                "i": 0.76986,
                "Omega": 74.22988,
                "omega": 170.96424,
                "M0": 142.23860,
                "n": 0.01172580,
                "color": "lightblue",
                "size": 10,
                "radius": 25362 / 149597870.7
            },
            "海王星": {
                "a": 30.06896348,
                "e": 0.00858587,
                "i": 1.76917,
                "Omega": 131.72169,
                "omega": 44.97135,
                "M0": 260.24716,
                "n": 0.00599514,
                "color": "darkblue",
                "size": 10,
                "radius": 24622 / 149597870.7
            }
        }
    
    def date_to_julian_day(self, year, month, day):
        """
        将地球年月日转换为儒略日
        :param year: 年份
        :param month: 月份
        :param day: 日期
        :return: 儒略日
        """
        if month <= 2:
            year -= 1
            month += 12
        
        A = year // 100
        B = 2 - A + A // 4
        
        julian_day = 365.25 * (year + 4716) + 30.6001 * (month + 1) + day + B - 1524.5
        return julian_day
    
    def julian_day_to_date(self, julian_day):
        """
        将儒略日转换为地球年月日
        :param julian_day: 儒略日
        :return: (year, month, day)
        """
        julian_day += 0.5
        Z = int(julian_day)
        F = julian_day - Z
        
        if Z < 2299161:
            A = Z
        else:
            alpha = int((Z - 1867216.25) / 36524.25)
            A = Z + 1 + alpha - alpha // 4
        
        B = A + 1524
        C = int((B - 122.1) / 365.25)
        D = int(365.25 * C)
        E = int((B - D) / 30.6001)
        
        day = B - D - int(30.6001 * E) + F
        month = E - 1 if E < 14 else E - 13
        year = C - 4716 if month > 2 else C - 4715
        
        return int(year), int(month), day
    
    def calculate_mean_anomaly(self, M0, n, delta_days):
        """
        计算给定时间的平近点角
        :param M0: 初始平近点角（度）
        :param n: 平均角速度（度/天）
        :param delta_days: 与历元的天数差
        :return: 平近点角（度）
        """
        return (M0 + n * delta_days) % 360
    
    def solve_kepler_equation(self, M, e):
        """
        解开普勒方程：M = E - e*sin(E)
        :param M: 平近点角（弧度）
        :param e: 偏心率
        :return: 偏近点角（弧度）
        """
        E = M if e < 0.8 else np.pi
        for i in range(10):
            E = E - (E - e * np.sin(E) - M) / (1 - e * np.cos(E))
        return E
    
    def calculate_body_position(self, body_name, year=None, month=None, day=None, julian_day=None):
        """
        计算给定日期星体的位置
        :param body_name: 星体名称
        :param year: 年份（可选，如果提供了julian_day则忽略）
        :param month: 月份（可选，如果提供了julian_day则忽略）
        :param day: 日期（可选，如果提供了julian_day则忽略）
        :param julian_day: 儒略日（可选，如果提供则直接使用）
        :return: (x, y, z) 日心直角坐标系位置（AU）
        """
        if body_name not in self.bodies:
            raise ValueError(f"未知星体: {body_name}")
        
        # 获取星体轨道参数
        body = self.bodies[body_name]
        a = body["a"]
        e = body["e"]
        i = np.radians(body["i"])
        Omega = np.radians(body["Omega"])
        omega = np.radians(body["omega"])
        M0 = np.radians(body["M0"])
        n = body["n"]
        
        # 计算与J2000历元的天数差
        jd_j2000 = self.date_to_julian_day(2000, 1, 1)
        if julian_day is not None:
            jd_target = julian_day
        else:
            jd_target = self.date_to_julian_day(year, month, day)
        delta_days = jd_target - jd_j2000
        
        # 计算平近点角
        M_deg = self.calculate_mean_anomaly(np.degrees(M0), n, delta_days)
        M = np.radians(M_deg)
        
        # 解开普勒方程得到偏近点角
        E = self.solve_kepler_equation(M, e)
        
        # 计算真近点角
        nu = 2 * np.arctan2(np.sqrt(1 + e) * np.sin(E/2), np.sqrt(1 - e) * np.cos(E/2))
        
        # 计算轨道半径
        r = a * (1 - e * np.cos(E))
        
        # 计算轨道平面内的位置（考虑近心点经度）
        longitude = omega + nu
        x_orb = r * np.cos(longitude)
        y_orb = r * np.sin(longitude)
        z_orb = 0.0
        
        # 坐标变换：轨道平面 -> 黄道平面
        # 1. 绕x轴旋转-倾角i
        x1 = x_orb
        y1 = y_orb * np.cos(-i) - z_orb * np.sin(-i)
        z1 = y_orb * np.sin(-i) + z_orb * np.cos(-i)
        
        # 2. 绕z轴旋转升交点经度Omega
        x2 = x1 * np.cos(Omega) - y1 * np.sin(Omega)
        y2 = x1 * np.sin(Omega) + y1 * np.cos(Omega)
        z2 = z1
        
        return x2, y2, z2
    
    def calculate_body_velocity(self, body_name, year=None, month=None, day=None, julian_day=None):
        """
        计算给定日期星体的速度
        :param body_name: 星体名称
        :param year: 年份（可选，如果提供了julian_day则忽略）
        :param month: 月份（可选，如果提供了julian_day则忽略）
        :param day: 日期（可选，如果提供了julian_day则忽略）
        :param julian_day: 儒略日（可选，如果提供则直接使用）
        :return: (vx, vy, vz) 日心直角坐标系速度（AU/天）
        """
        if body_name not in self.bodies:
            raise ValueError(f"未知星体: {body_name}")
        
        # 获取星体轨道参数
        body = self.bodies[body_name]
        a = body["a"]
        e = body["e"]
        i = np.radians(body["i"])
        Omega = np.radians(body["Omega"])
        omega = np.radians(body["omega"])
        M0 = np.radians(body["M0"])
        n = body["n"]
        
        # 计算与J2000历元的天数差
        jd_j2000 = self.date_to_julian_day(2000, 1, 1)
        if julian_day is not None:
            jd_target = julian_day
        else:
            jd_target = self.date_to_julian_day(year, month, day)
        delta_days = jd_target - jd_j2000
        
        # 计算平近点角
        M_deg = self.calculate_mean_anomaly(np.degrees(M0), n, delta_days)
        M = np.radians(M_deg)
        
        # 解开普勒方程得到偏近点角
        E = self.solve_kepler_equation(M, e)
        
        # 计算真近点角
        nu = 2 * np.arctan2(np.sqrt(1 + e) * np.sin(E/2), np.sqrt(1 - e) * np.cos(E/2))
        
        # 计算轨道半径
        r = a * (1 - e * np.cos(E))
        
        # 计算轨道平面内的速度分量
        # 太阳系引力常数 (AU^3/天^2)
        G = 1.32712440018e20  # m^3/s^2
        AU = 149597870700  # m
        day_in_seconds = 86400  # 秒/天
        
        # 转换为AU^3/天^2
        mu = G * (day_in_seconds ** 2) / (AU ** 3)  # 太阳引力常数
        
        # 计算偏近点角的导数
        dE_dt = np.sqrt(mu / (a ** 3)) / (1 - e * np.cos(E))
        
        # 计算轨道平面内的速度分量
        v_r = a * e * np.sin(E) * dE_dt
        v_theta = r * np.sqrt(mu / (a ** 3)) * (1 + e * np.cos(nu)) / (1 - e ** 2)
        
        # 基于近心点经度：omega + nu
        longitude = omega + nu
        
        # 转换为轨道平面内的笛卡尔速度分量
        vx_orb = v_r * np.cos(longitude) - v_theta * np.sin(longitude)
        vy_orb = v_r * np.sin(longitude) + v_theta * np.cos(longitude)
        vz_orb = 0.0
        
        # 坐标变换：轨道平面 -> 黄道平面
        # 1. 绕x轴旋转-倾角i
        vx1 = vx_orb
        vy1 = vy_orb * np.cos(-i) - vz_orb * np.sin(-i)
        vz1 = vy_orb * np.sin(-i) + vz_orb * np.cos(-i)
        
        # 2. 绕z轴旋转升交点经度Omega
        vx2 = vx1 * np.cos(Omega) - vy1 * np.sin(Omega)
        vy2 = vx1 * np.sin(Omega) + vy1 * np.cos(Omega)
        vz2 = vz1
        
        return vx2, vy2, vz2
    
    def calculate_all_bodies_positions(self, year, month, day):
        """
        计算给定日期所有太阳系主要星体的位置
        :param year: 年份
        :param month: 月份
        :param day: 日期
        :return: 字典，键为星体名称，值为(x, y, z)位置
        """
        positions = {}
        for body_name in self.bodies:
            if body_name == "太阳":
                positions[body_name] = (0.0, 0.0, 0.0)
            else:
                positions[body_name] = self.calculate_body_position(body_name, year, month, day)
        return positions
    
    
    def plot_solar_system_enhanced(self, year, month, day, view_3d=True, ax=None):
        """
        美化的太阳系绘制，添加太空环境效果
        :param year: 年份
        :param month: 月份
        :param day: 日期
        :param view_3d: 是否使用3D视图
        :param ax: 可选的matplotlib轴对象，如果提供则在该轴上绘制
        """
        # 用于存储光标对象的列表
        cursors = []
        
        # 如果没有提供轴，则创建新的图形
        if ax is None:
            # 创建图形
            fig = plt.figure(figsize=(14, 10))
            # #关闭坐标轴
            # plt.axis('off')
            # #关闭网格
            # plt.grid(None)
            
            if view_3d:
                ax = fig.add_subplot(111, projection='3d')
                ax.set_facecolor('black')
                fig.patch.set_facecolor('black')
                ax.xaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
                ax.yaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
                ax.zaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
                ax.grid(False)
            else:
                ax = fig.add_subplot(111)
                ax.set_aspect('equal')
                ax.set_facecolor('black')
                fig.patch.set_facecolor('black')
            return_fig = fig
        else:
            # 清除轴的内容
            ax.clear()
            # 设置轴的属性
            if view_3d:
                ax.set_facecolor('black')
                ax.xaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
                ax.yaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
                ax.zaxis.set_pane_color((0.0, 0.0, 0.0, 0.0))
                ax.grid(False)
            else:
                ax.set_aspect('equal')
                ax.set_facecolor('black')
            return_fig = ax.get_figure()
        
        # 计算并绘制每个星体
        for body_name, body in self.bodies.items():
            if body_name == "太阳":
                continue
            
            try:
                # 获取星体位置
                x, y, z = self.calculate_body_position(body_name, year, month, day)
                
                # 绘制星体
                if view_3d:
                    scatter = ax.scatter(x, y, z, color=body["color"], s=body["size"]*2, label=body_name)
                else:
                    scatter = ax.scatter(x, y, color=body["color"], s=body["size"]*2, label=body_name)
                
                # 为散点添加光标悬停效果
                cursor = mplcursors.cursor(scatter, hover=True)
                cursors.append(cursor)
                @cursor.connect("add")
                def on_add(sel, name=body_name, body_data=body):
                    # 构建提示信息
                    # 左对齐文本
                    info = f"{name}\n"
                    info += f"半长轴: {body_data['a']:.3f} AU\n"
                    info += f"偏心率: {body_data['e']:.3f}\n"
                    info += f"轨道倾角: {body_data['i']:.2f}°\n"
                    # 设置文本左对齐
                    sel.annotation.set_ha('left')

                    sel.annotation.set_text(info)
                    sel.annotation.get_bbox_patch().set(fc="lightgray", ec="black", alpha=0.8)
                


                # 绘制轨道
                a = body["a"]
                e = body["e"]
                i = np.radians(body["i"])
                Omega = np.radians(body["Omega"])
                omega = np.radians(body["omega"])
                
                # 生成轨道点
                nu_list = np.linspace(0, 2*np.pi, 100)
                
                x_orbit = []
                y_orbit = []
                z_orbit = []
                
                for nu in nu_list:
                    # 计算近心点经度：omega + nu
                    longitude = omega + nu
                    r = a * (1 - e**2) / (1 + e * np.cos(nu))
                    x_orb = r * np.cos(longitude)
                    y_orb = r * np.sin(longitude)
                    z_orb = 0.0
                    
                    # 坐标变换
                    # 1. 绕x轴旋转-倾角i
                    x1 = x_orb
                    y1 = y_orb * np.cos(-i) - z_orb * np.sin(-i)
                    z1 = y_orb * np.sin(-i) + z_orb * np.cos(-i)
                    
                    # 2. 绕z轴旋转升交点经度Omega
                    x2 = x1 * np.cos(Omega) - y1 * np.sin(Omega)
                    y2 = x1 * np.sin(Omega) + y1 * np.cos(Omega)
                    z2 = z1
                    
                    x_orbit.append(x2)
                    y_orbit.append(y2)
                    z_orbit.append(z2)
                
                # 绘制轨道
                if view_3d:
                    ax.plot(x_orbit, y_orbit, z_orbit, color=body["color"], alpha=0.6)
                else:
                    ax.plot(x_orbit, y_orbit, color=body["color"], alpha=0.6)
                    
            except Exception as e:
                print(f"绘制{body_name}时出错: {e}")
        
        # 绘制太阳
        if view_3d:
            sun_scatter = ax.scatter(0, 0, 0, color=self.bodies["太阳"]["color"], s=200, label="太阳")
        else:
            sun_scatter = ax.scatter(0, 0, color=self.bodies["太阳"]["color"], s=200, label="太阳")
        
        # 为太阳添加光标悬停效果
        sun_cursor = mplcursors.cursor(sun_scatter, hover=True)
        cursors.append(sun_cursor)
        @sun_cursor.connect("add")
        def on_add_sun(sel):
            body = self.bodies["太阳"]
            info = f"太阳\n"
            info += f"半径: {body['radius']*149597870.7:.0f} km\n"
            info += f"质量：1.989e30 kg\n"
            sel.annotation.set_ha('left')
            sel.annotation.set_text(info)
            sel.annotation.get_bbox_patch().set(fc="lightgray", ec="black", alpha=0.8)
        
        # 设置标题和标签
        time_str = f"{year}-{month:02d}-{day:02d}"
        if view_3d:
            ax.set_title(f"太阳系 ({time_str})", color='white', fontsize=16)
        else:
            ax.set_title(f"太阳系 ({time_str})", color='white', fontsize=16)
        
        # 设置坐标轴范围
        max_dist = 35  # AU，覆盖海王星轨道
        if view_3d:
            ax.set_xlim(-max_dist, max_dist)
            ax.set_ylim(-max_dist, max_dist)
            ax.set_zlim(-max_dist, max_dist)
        else:
            ax.set_xlim(-max_dist, max_dist)
            ax.set_ylim(-max_dist, max_dist)
        
        # 不添加图例
        # legend = ax.legend(loc='upper left', fontsize=12)
        # for text in legend.get_texts():
        #     text.set_color('white')
        
        plt.tight_layout()
        return return_fig, ax, cursors

if __name__ == "__main__":
    print("开始测试太阳系模型...")
    try:
        # 创建太阳系模型实例
        solar_system = SolarSystem()
        
        # 绘制美化的太阳系
        print("\n绘制美化的太阳系...")
        fig, ax, _ = solar_system.plot_solar_system_enhanced(2300, 1, 1, view_3d=True)
        plt.savefig('SolarSystem_Enhanced_3D.png', facecolor='black', dpi=300)
        print("美化的3D太阳系视图已保存为 SolarSystem_Enhanced_3D.png")
        
        # 测试行星位置计算
        print("\n测试行星位置计算...")
        earth_pos = solar_system.calculate_body_position("地球", 2023, 1, 1)
        print(f"地球位置 (2023-01-01): {earth_pos}")
        
        # 测试行星速度计算
        print("\n测试行星速度计算...")
        earth_vel = solar_system.calculate_body_velocity("地球", 2023, 1, 1)
        print(f"地球速度 (2023-01-01): {earth_vel}")
        
        print("\n测试完成！")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()