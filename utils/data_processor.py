import numpy as np
import pandas as pd
import os
from utils.config import Config

class DataProcessor:
    """数据处理类"""
    
    def __init__(self):
        """初始化数据处理器"""
        self.config = Config()
        self.config.ensure_output_directories()
    
    def save_trajectory_data(self, solution, filename):
        """
        保存轨迹数据
        :param solution: 轨迹状态向量
        :param filename: 文件名
        """
        # 确保输出目录存在
        output_dir = self.config.get('output.directory', 'Output')
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存数据
        filepath = os.path.join(output_dir, filename)
        np.savetxt(filepath, solution, delimiter=',')
        print(f"轨迹数据已保存到 {filepath}")
    
    def load_trajectory_data(self, filename):
        """
        加载轨迹数据
        :param filename: 文件名
        :return: 轨迹状态向量
        """
        # 构建文件路径
        output_dir = self.config.get('output.directory', 'Output')
        filepath = os.path.join(output_dir, filename)
        
        # 加载数据
        if os.path.exists(filepath):
            solution = np.loadtxt(filepath, delimiter=',')
            return solution
        else:
            raise FileNotFoundError(f"文件不存在: {filepath}")
    
    def save_porkchop_data(self, df, filename='porkchop_results.csv'):
        """
        保存猪排图数据
        :param df: 猪排图数据DataFrame
        :param filename: 文件名
        """
        # 确保输出目录存在
        output_dir = self.config.get('output.directory', 'Output')
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存数据
        filepath = os.path.join(output_dir, filename)
        df.to_csv(filepath, float_format='%.4f')
        print(f"猪排图数据已保存到 {filepath}")
    
    def load_porkchop_data(self, filename='porkchop_results.csv'):
        """
        加载猪排图数据
        :param filename: 文件名
        :return: 猪排图数据DataFrame
        """
        # 构建文件路径
        output_dir = self.config.get('output.directory', 'Output')
        filepath = os.path.join(output_dir, filename)
        
        # 加载数据
        if os.path.exists(filepath):
            df = pd.read_csv(filepath, index_col=0)
            return df
        else:
            raise FileNotFoundError(f"文件不存在: {filepath}")
    
    def process_trajectory_data(self, solution, N):
        """
        处理轨迹数据
        :param solution: 轨迹状态向量
        :param N: 网格数
        :return: 处理后的轨迹数据字典
        """
        # 提取位置数据
        x_pos = solution[:N]
        y_pos = solution[N:2*N]
        z_pos = solution[2*N:3*N]
        
        # 提取速度数据
        vx = solution[3*N:4*N]
        vy = solution[4*N:5*N]
        vz = solution[5*N:6*N]
        
        # 提取控制输入数据
        ux = solution[6*N:7*N]
        uy = solution[7*N:8*N]
        uz = solution[8*N:9*N]
        
        # 计算速度大小
        v_mag = np.sqrt(vx**2 + vy**2 + vz**2)
        
        # 计算控制输入大小
        u_mag = np.sqrt(ux**2 + uy**2 + uz**2)
        
        # 构建数据字典
        trajectory_data = {
            'position': {
                'x': x_pos,
                'y': y_pos,
                'z': z_pos
            },
            'velocity': {
                'vx': vx,
                'vy': vy,
                'vz': vz,
                'magnitude': v_mag
            },
            'control': {
                'ux': ux,
                'uy': uy,
                'uz': uz,
                'magnitude': u_mag
            }
        }
        
        return trajectory_data
    
    def generate_trajectory_report(self, trajectory_data, dv, departure_body, arrival_body, 
                                 departure_time, arrival_time, tof_years):
        """
        生成轨迹报告
        :param trajectory_data: 处理后的轨迹数据
        :param dv: 速度增量 (km/s)
        :param departure_body: 出发星体
        :param arrival_body: 到达星体
        :param departure_time: 出发时间
        :param arrival_time: 到达时间
        :param tof_years: 飞行时间 (年)
        :return: 轨迹报告字符串
        """
        # 计算轨迹长度
        x = trajectory_data['position']['x']
        y = trajectory_data['position']['y']
        z = trajectory_data['position']['z']
        
        trajectory_length = 0
        for i in range(1, len(x)):
            dx = x[i] - x[i-1]
            dy = y[i] - y[i-1]
            dz = z[i] - z[i-1]
            trajectory_length += np.sqrt(dx**2 + dy**2 + dz**2)
        
        # 计算最大速度
        max_velocity = np.max(trajectory_data['velocity']['magnitude'])
        
        # 计算最大控制输入
        max_control = np.max(trajectory_data['control']['magnitude'])
        
        # 构建报告
        report = f"=== 轨迹报告 ===\n"
        report += f"出发星体: {departure_body}\n"
        report += f"到达星体: {arrival_body}\n"
        report += f"出发时间: {departure_time}\n"
        report += f"到达时间: {arrival_time}\n"
        report += f"飞行时间: {tof_years:.2f} 年\n"
        report += f"速度增量: {dv:.4f} km/s\n"
        report += f"轨迹长度: {trajectory_length:.4f} AU\n"
        report += f"最大速度: {max_velocity:.4f} AU/year\n"
        report += f"最大控制输入: {max_control:.4f} AU/year²\n"
        report += "==================\n"
        
        return report
    
    def save_trajectory_report(self, report, filename):
        """
        保存轨迹报告
        :param report: 轨迹报告字符串
        :param filename: 文件名
        """
        # 确保输出目录存在
        output_dir = self.config.get('output.directory', 'Output')
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存报告
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"轨迹报告已保存到 {filepath}")
    
    def analyze_porkchop_data(self, df):
        """
        分析猪排图数据
        :param df: 猪排图数据DataFrame
        :return: 分析结果字典
        """
        # 提取数据
        dv_values = df.values
        
        # 计算最小值和位置
        min_dv = np.min(dv_values[np.isfinite(dv_values)])
        min_pos = np.where(dv_values == min_dv)
        
        if len(min_pos[0]) > 0:
            min_year = df.index[min_pos[0][0]]
            min_tof = float(df.columns[min_pos[1][0]].strip('y'))
        else:
            min_year = None
            min_tof = None
        
        # 计算平均值和标准差
        mean_dv = np.mean(dv_values[np.isfinite(dv_values)])
        std_dv = np.std(dv_values[np.isfinite(dv_values)])
        
        # 构建分析结果
        analysis = {
            'min_dv': min_dv,
            'min_year': min_year,
            'min_tof': min_tof,
            'mean_dv': mean_dv,
            'std_dv': std_dv,
            'shape': df.shape
        }
        
        return analysis
    
    def generate_porkchop_report(self, analysis, departure_body, arrival_body):
        """
        生成猪排图分析报告
        :param analysis: 分析结果字典
        :param departure_body: 出发星体
        :param arrival_body: 到达星体
        :return: 分析报告字符串
        """
        report = f"=== 猪排图分析报告 ===\n"
        report += f"出发星体: {departure_body}\n"
        report += f"到达星体: {arrival_body}\n"
        report += f"最小速度增量: {analysis['min_dv']:.4f} km/s\n"
        if analysis['min_year'] and analysis['min_tof']:
            report += f"最优发射窗口: {analysis['min_year']}年，飞行时间 {analysis['min_tof']}年\n"
        report += f"平均速度增量: {analysis['mean_dv']:.4f} km/s\n"
        report += f"速度增量标准差: {analysis['std_dv']:.4f} km/s\n"
        report += f"数据点数量: {analysis['shape'][0]}×{analysis['shape'][1]}\n"
        report += "=====================\n"
        
        return report
    
    def save_porkchop_report(self, report, filename):
        """
        保存猪排图分析报告
        :param report: 分析报告字符串
        :param filename: 文件名
        """
        # 确保输出目录存在
        output_dir = self.config.get('output.directory', 'Output')
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存报告
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"猪排图分析报告已保存到 {filepath}")

if __name__ == "__main__":
    """测试数据处理功能"""
    data_processor = DataProcessor()
    print("数据处理器初始化完成")
    
    # 测试保存和加载轨迹数据
    print("\n测试保存和加载轨迹数据:")
    test_solution = np.random.rand(900)  # 100网格的轨迹数据
    data_processor.save_trajectory_data(test_solution, 'test_trajectory.csv')
    loaded_solution = data_processor.load_trajectory_data('test_trajectory.csv')
    print(f"保存和加载的数据形状: {loaded_solution.shape}")
    
    # 测试处理轨迹数据
    print("\n测试处理轨迹数据:")
    trajectory_data = data_processor.process_trajectory_data(test_solution, 100)
    print(f"轨迹数据处理完成，位置数据形状: {trajectory_data['position']['x'].shape}")
    
    # 测试生成轨迹报告
    print("\n测试生成轨迹报告:")
    report = data_processor.generate_trajectory_report(
        trajectory_data,
        10.5,
        "木星",
        "海王星",
        "2300-06-01",
        "2302-06-01",
        2
    )
    print(report)
