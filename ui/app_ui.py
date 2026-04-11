import streamlit as st
import numpy as np
from datetime import datetime, timedelta
from core.solar_system import SolarSystem
import plotly.graph_objects as go
from Param import PLANET_SIZE_SCALE, BASE_SIZE, MAX_DISTANCE, ORBIT_LINE_WIDTH, CHART_CONFIG

class SolarSystemUI:
    """太阳系可视化UI类"""
    
    def __init__(self):
        """初始化UI"""
        # 设置页面配置
        st.set_page_config(
            page_title="太阳系轨道设计工具",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # 添加CSS样式
        st.markdown("""<style>
            /* 调整主容器 */
            .block-container { 
                padding: 1rem !important;
                margin: 0 !important;
                max-width: 100% !important;
            }
            
            /* 移除页面边距和背景 */
            body {
                margin: 0 !important;
                padding: 0 !important;
                background-color: #000000 !important;
            }
            
            /* 调整标题样式 */
            h1 {
                margin-bottom: 1rem !important;
                color: white;
            }
            
            /* 调整滑块和日期显示的样式 */
            .stSlider {
                margin-bottom: 1rem !important;
                background-color: rgba(0, 0, 0, 0.7);
                padding: 1rem;
                border-radius: 5px;
            }
            
            .stMarkdown {
                margin-bottom: 1rem !important;
                background-color: rgba(0, 0, 0, 0.7);
                padding: 1rem;
                border-radius: 5px;
                color: white;
            }
            
            /* 调整滑块标签颜色 */
            .stSlider label {
                color: white !important;
            }
            
            /* 调整滑块值颜色 */
            .stSlider div div div div {
                color: white !important;
            }
            
            /* 调整Plotly图表 */
            .stPlotlyChart {
                width: 100% !important;
                height: 80vh !important;
            }
        </style>""", unsafe_allow_html=True)
        
        # 创建太阳系模型实例
        self.solar_system = SolarSystem()
    
    def render(self):
        """渲染UI"""
        # 初始化会话状态
        if 'camera' not in st.session_state:
            st.session_state.camera = dict(
                up=dict(x=0, y=1, z=0),
                eye=dict(x=0, y=0, z=1.5)
            )
        
        # 页面标题
        st.title("太阳系轨道设计工具")
        
        # 日期调整滑块
        days = st.slider(
            "时间调整（天）",
            min_value=-365,
            max_value=365,
            value=0,
            step=1,
            help="调整日期，正值为未来，负值为过去"
        )
        
        # 计算调整后的基础日期
        base_date = datetime.now() + timedelta(days=days)
        
        # 显示当前日期
        st.write(f"当前日期: {base_date.year}-{base_date.month:02d}-{base_date.day:0.2f}")
        
        # 图表容器
        chart_container = st.empty()
        
        # 创建太阳系可视化图表（带动画）
        fig = self.create_solar_system_figure(base_date, st.session_state.camera)
        
        # 显示图表
        chart_container.plotly_chart(fig, width='stretch', config={'displayModeBar': False, 'scrollZoom': True})
    
    def create_solar_system_figure(self, base_date, camera=None):
        """
        创建太阳系可视化图表
        :param base_date: 基础日期
        :param camera: 相机视角参数
        :return: Plotly 图表对象
        """
        # 保存当前相机视角
        if camera is None:
            camera = dict(
                up=dict(x=0, y=1, z=0),
                eye=dict(x=0, y=0, z=1.5)
            )
        
        # 创建图表
        fig = go.Figure()

        # 调整图片大小
        fig.update_layout(
            width=1200,
            height=1000,
            scene=dict(
                aspectratio=dict(x=1, y=1, z=1),
                camera=camera
            )
        )
        
        # 绘制太阳（固定位置）
        sun_size = BASE_SIZE * PLANET_SIZE_SCALE["太阳"]
        fig.add_trace(go.Scatter3d(
            x=[0], y=[0], z=[0],
            mode='markers',
            marker=dict(size=sun_size, color='orange'),
            name='太阳',
            hoverinfo='name'
        ))
        
        # 为每个行星创建轨迹和轨道
        for body_name in self.solar_system.bodies:
            if body_name == "太阳":
                continue
            
            body = self.solar_system.bodies[body_name]
            color = body["color"]
            size = BASE_SIZE * PLANET_SIZE_SCALE[body_name]
            
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
            
            # 添加轨道轨迹
            orbit_trace = go.Scatter3d(
                x=x_orbit, y=y_orbit, z=z_orbit,
                mode='lines',
                line=dict(color=color, width=ORBIT_LINE_WIDTH),
                name=f'{body_name} 轨道',
                hoverinfo='name'
            )
            fig.add_trace(orbit_trace)
            
            # 添加行星轨迹（当前位置）
            jd = self.solar_system.date_to_julian_day(
                base_date.year,
                base_date.month,
                base_date.day
            )
            x, y, z = self.solar_system.calculate_body_position(body_name, julian_day=jd)
            
            planet_trace = go.Scatter3d(
                x=[x], y=[y], z=[z],
                mode='markers',
                marker=dict(size=size, color=color),
                name=body_name,
                hoverinfo='name'
            )
            fig.add_trace(planet_trace)
        
        # 配置图表
        fig.update_layout(
            scene=dict(
                bgcolor=CHART_CONFIG["bg_color"],
                xaxis=dict(
                    showgrid=CHART_CONFIG["show_grid"],
                    visible=CHART_CONFIG["show_axes"],
                    gridcolor='#333333'
                ),
                yaxis=dict(
                    showgrid=CHART_CONFIG["show_grid"],
                    visible=CHART_CONFIG["show_axes"],
                    gridcolor='#333333'
                ),
                zaxis=dict(
                    showgrid=CHART_CONFIG["show_grid"],
                    visible=CHART_CONFIG["show_axes"],
                    gridcolor='#333333'
                ),
                aspectmode='cube'
            ),
            paper_bgcolor=CHART_CONFIG["paper_bg_color"],
            plot_bgcolor=CHART_CONFIG["paper_bg_color"],
            showlegend=False  # 去掉图例显示
        )
        
        # 设置坐标轴范围
        fig.update_scenes(
            xaxis=dict(range=[-MAX_DISTANCE, MAX_DISTANCE]),
            yaxis=dict(range=[-MAX_DISTANCE, MAX_DISTANCE]),
            zaxis=dict(range=[-MAX_DISTANCE, MAX_DISTANCE])
        )
        
        # 移除图表周围的空白和背景
        fig.update_layout(margin=dict(l=0, r=0, b=0, t=0))
        
        return fig
