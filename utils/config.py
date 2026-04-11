import json
import os

class Config:
    """配置管理类"""
    
    def __init__(self, config_file='config.json'):
        """
        初始化配置管理器
        :param config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self):
        """
        加载配置文件
        :return: 配置字典
        """
        default_config = {
            "solar_system": {
                "mu": 4 * 3.141592653589793 ** 2,  # 太阳引力常数 (AU^3/year^2)
                "bodies": ["太阳", "水星", "金星", "地球", "火星", "木星", "土星", "天王星", "海王星"]
            },
            "trajectory": {
                "default_N": 50,  # 默认网格数
                "default_rbound_factor": 0.5,  # 默认半径边界因子
                "max_iterations": 50,  # 优化最大迭代次数
                "ftol": 1e-12  # 优化收敛 tolerance
            },
            "visualization": {
                "figure_size": [14, 10],  # 图形大小
                "dpi": 300,  # 图形DPI
                "default_view": "3D"  # 默认视图类型
            },
            "porkchop": {
                "default_start_year": 2300,  # 默认起始年份
                "default_end_year": 2350,  # 默认结束年份
                "default_tof_min": 1,  # 默认最小飞行时间
                "default_tof_max": 10,  # 默认最大飞行时间
                "default_N": 30  # 默认网格数
            },
            "output": {
                "directory": "Output",  # 输出目录
                "porkchop_directory": "Output/PorkChop"  # 猪排图输出目录
            }
        }
        
        # 如果配置文件存在，加载它
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 合并默认配置和用户配置
                return self._merge_configs(default_config, config)
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return default_config
        else:
            # 保存默认配置
            self.save_config(default_config)
            return default_config
    
    def _merge_configs(self, default, user):
        """
        合并默认配置和用户配置
        :param default: 默认配置
        :param user: 用户配置
        :return: 合并后的配置
        """
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self._merge_configs(default[key], value)
            else:
                default[key] = value
        return default
    
    def save_config(self, config=None):
        """
        保存配置到文件
        :param config: 要保存的配置，如果为None则保存当前配置
        """
        if config is None:
            config = self.config
        
        # 确保配置文件所在目录存在
        os.makedirs(os.path.dirname(os.path.abspath(self.config_file)), exist_ok=True)
        
        # 保存配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    def get(self, key, default=None):
        """
        获取配置值
        :param key: 配置键，支持点分隔路径，如 "solar_system.mu"
        :param default: 默认值
        :return: 配置值
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """
        设置配置值
        :param key: 配置键，支持点分隔路径，如 "solar_system.mu"
        :param value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        # 遍历到最后一个键的父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
        
        # 保存配置
        self.save_config()
    
    def get_solar_system_config(self):
        """
        获取太阳系配置
        :return: 太阳系配置字典
        """
        return self.get('solar_system', {})
    
    def get_trajectory_config(self):
        """
        获取轨迹配置
        :return: 轨迹配置字典
        """
        return self.get('trajectory', {})
    
    def get_visualization_config(self):
        """
        获取可视化配置
        :return: 可视化配置字典
        """
        return self.get('visualization', {})
    
    def get_porkchop_config(self):
        """
        获取猪排图配置
        :return: 猪排图配置字典
        """
        return self.get('porkchop', {})
    
    def get_output_config(self):
        """
        获取输出配置
        :return: 输出配置字典
        """
        return self.get('output', {})
    
    def ensure_output_directories(self):
        """
        确保输出目录存在
        """
        output_config = self.get_output_config()
        
        # 确保主输出目录存在
        output_dir = output_config.get('directory', 'Output')
        os.makedirs(output_dir, exist_ok=True)
        
        # 确保猪排图输出目录存在
        porkchop_dir = output_config.get('porkchop_directory', 'Output/PorkChop')
        os.makedirs(porkchop_dir, exist_ok=True)

if __name__ == "__main__":
    """测试配置管理"""
    config = Config()
    print("当前配置:")
    print(json.dumps(config.config, indent=4, ensure_ascii=False))
    
    # 测试获取配置
    print("\n测试获取配置:")
    print(f"太阳引力常数: {config.get('solar_system.mu')}")
    print(f"默认网格数: {config.get('trajectory.default_N')}")
    
    # 测试设置配置
    print("\n测试设置配置:")
    config.set('trajectory.default_N', 100)
    print(f"更新后默认网格数: {config.get('trajectory.default_N')}")
    
    # 测试确保输出目录
    print("\n测试确保输出目录:")
    config.ensure_output_directories()
    print("输出目录已确保存在")
