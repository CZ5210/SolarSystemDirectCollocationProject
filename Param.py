# 可视化参数配置

# 行星大小缩放因子
PLANET_SIZE_SCALE = {
    "太阳": 0.3,      # 太阳大小
    "水星": 0.15,      # 水星大小
    "金星": 0.15,      # 金星大小
    "地球": 0.15,      # 地球大小
    "火星": 0.15,     # 火星大小
    "木星": 0.15,      # 木星大小
    "土星": 0.15,      # 土星大小
    "天王星": 0.15,    # 天王星大小
    "海王星": 0.15      # 海王星大小
}

# 基础大小
BASE_SIZE = 10

# 最大显示距离（AU）
MAX_DISTANCE = 35

# 轨道线条宽度
ORBIT_LINE_WIDTH = 2

# 图表配置
CHART_CONFIG = {
    "show_grid": False,  # 是否显示网格
    "show_axes": False,  # 是否显示坐标轴
    "bg_color": "black",  # 背景颜色
    "paper_bg_color": "#2d2d2d",  # 纸张背景颜色
    "legend_bg_color": "#2d2d2d",  # 图例背景颜色
    "text_color": "white"  # 文本颜色
}

# 时间参数配置
TIME_CONFIG = {
    "min_days": 0,  # 最小天数（只能前进）
    "max_days": 365*5,  # 最大天数
    "default_days": 0,  # 默认天数
    "step": 10  # 步长
}
