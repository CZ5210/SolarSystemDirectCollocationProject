#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit应用 - 太阳系轨道设计工具
"""

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from core.solar_system import SolarSystem
from core.trajectory_optimizer import TrajectoryOptimizer
from core.visualization import Visualization
from features.orbit_planner import OrbitPlanner
from features.porkchop import Porkchop
from features.direction_optimizer import DirectionOptimizer

# 初始化功能模块
planner = OrbitPlanner()
solar_system = SolarSystem()
optimizer = TrajectoryOptimizer()
visualization = Visualization()
porkchop_generator = Porkchop()
direction_optimizer = DirectionOptimizer()

# 设置页面配置
st.set_page_config(
    page_title="太阳系轨道设计工具",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 页面标题
st.title("太阳系轨道设计工具")

# 侧边栏导航
page = st.sidebar.selectbox(
    "选择功能",
    ["太阳系可视化", "轨道规划", "发射窗口分析", "方向优化"]
)

# 太阳系可视化页面
if page == "太阳系可视化":
    st.header("太阳系可视化")
    
    # 获取当前日期
    current_date = datetime.now()
    
    # 日期选择器
    col1, col2, col3 = st.columns(3)
    with col1:
        year = st.number_input("年份", min_value=2000, max_value=2500, value=current_date.year)
    with col2:
        month = st.number_input("月份", min_value=1, max_value=12, value=current_date.month)
    with col3:
        day = st.number_input("日期", min_value=1, max_value=31, value=current_date.day)
    
    # 视图类型选择
    view_type = st.selectbox("视图类型", ["2D", "3D"])
    
    # 绘制按钮
    if st.button("绘制太阳系"):
        try:
            # 绘制太阳系
            fig, ax = solar_system.plot_solar_system_enhanced(year, month, day, view_3d=view_type == "3D")
            st.pyplot(fig)
        except Exception as e:
            st.error(f"绘制过程中出现错误: {e}")

# 轨道规划页面
elif page == "轨道规划":
    st.header("轨道规划")
    
    # 获取当前日期
    current_date = datetime.now()
    
    # 日期选择器
    col1, col2, col3 = st.columns(3)
    with col1:
        start_year = st.number_input("出发年份", min_value=2000, max_value=2500, value=current_date.year)
    with col2:
        start_month = st.number_input("月份", min_value=1, max_value=12, value=current_date.month)
    with col3:
        start_day = st.number_input("日期", min_value=1, max_value=31, value=current_date.day)
    
    # 飞行时间
    tof_years = st.number_input("飞行时间(年)", min_value=0.1, max_value=20.0, value=2.0, step=0.1)
    
    # 星体选择
    col4, col5 = st.columns(2)
    with col4:
        departure_body = st.selectbox("出发星体", planner.get_planet_list(), index=planner.get_planet_list().index("木星"))
    with col5:
        arrival_body = st.selectbox("到达星体", planner.get_planet_list(), index=planner.get_planet_list().index("海王星"))
    
    # 高级参数
    with st.expander("高级参数"):
        N = st.number_input("网格数", min_value=10, max_value=200, value=50, step=10)
        rbound_factor = st.number_input("太阳距离约束因子", min_value=0.1, max_value=1.0, value=0.5, step=0.1)
        thrust_limit = st.number_input("推力限制(AU/year²)", min_value=0.0, max_value=10.0, value=0.0, step=0.1)
        thrust_limit = thrust_limit if thrust_limit > 0 else None
    
    # 计算按钮
    if st.button("计算轨道"):
        try:
            # 验证输入
            is_valid, message = planner.validate_input(
                start_year, start_month, start_day, tof_years, departure_body, arrival_body
            )
            if not is_valid:
                st.error(message)
            else:
                # 计算轨道
                dv = planner.plan_orbit(
                    start_year=start_year,
                    start_month=start_month,
                    start_day=start_day,
                    tof_years=tof_years,
                    departure_body=departure_body,
                    arrival_body=arrival_body,
                    N=N,
                    rbound_factor=rbound_factor,
                    thrust_limit=thrust_limit,
                    plot=True
                )
                st.success(f"轨道计算完成，速度增量: {dv:.4f} km/s")
        except Exception as e:
            st.error(f"计算过程中出现错误: {e}")

# 发射窗口分析页面
elif page == "发射窗口分析":
    st.header("发射窗口分析")
    
    # 星体选择
    col1, col2 = st.columns(2)
    with col1:
        porkchop_departure = st.selectbox("出发星体", planner.get_planet_list(), index=planner.get_planet_list().index("木星"))
    with col2:
        porkchop_arrival = st.selectbox("到达星体", planner.get_planet_list(), index=planner.get_planet_list().index("海王星"))
    
    # 年份范围
    col3, col4 = st.columns(2)
    with col3:
        porkchop_start_year = st.number_input("起始年份", min_value=2000, max_value=2500, value=2300)
    with col4:
        porkchop_end_year = st.number_input("结束年份", min_value=2000, max_value=2500, value=2350)
    
    # 飞行时间范围
    col5, col6 = st.columns(2)
    with col5:
        porkchop_tof_min = st.number_input("最小飞行时间(年)", min_value=0.1, max_value=20.0, value=1.0, step=0.1)
    with col6:
        porkchop_tof_max = st.number_input("最大飞行时间(年)", min_value=0.1, max_value=20.0, value=10.0, step=0.1)
    
    # 网格数
    N = st.number_input("网格数", min_value=10, max_value=100, value=30, step=10)
    
    # 计算按钮
    if st.button("计算发射窗口"):
        try:
            if porkchop_start_year >= porkchop_end_year:
                st.error("起始年份必须小于结束年份")
            elif porkchop_tof_min >= porkchop_tof_max:
                st.error("最小飞行时间必须小于最大飞行时间")
            else:
                # 计算猪排图数据
                planner.calculate_launch_window(
                    departure_body=porkchop_departure,
                    arrival_body=porkchop_arrival,
                    start_year=porkchop_start_year,
                    end_year=porkchop_end_year,
                    step_years=1,
                    tof_range=(porkchop_tof_min, porkchop_tof_max),
                    tof_step=1,
                    N=N
                )
                st.success("猪排图数据计算完成")
        except Exception as e:
            st.error(f"计算过程中出现错误: {e}")
    
    # 绘制猪排图按钮
    if st.button("绘制猪排图"):
        try:
            # 绘制猪排图
            porkchop_generator.plot_porkchop_contour(
                csv_path='porkchop_results.csv',
                save_path='porkchop_contour.png'
            )
            st.image('porkchop_contour.png')
        except Exception as e:
            st.error(f"绘制过程中出现错误: {e}")

# 方向优化页面
elif page == "方向优化":
    st.header("方向优化")
    
    # 获取当前日期
    current_date = datetime.now()
    
    # 日期选择器
    col1, col2, col3 = st.columns(3)
    with col1:
        dir_start_year = st.number_input("出发年份", min_value=2000, max_value=2500, value=current_date.year)
    with col2:
        dir_start_month = st.number_input("月份", min_value=1, max_value=12, value=current_date.month)
    with col3:
        dir_start_day = st.number_input("日期", min_value=1, max_value=31, value=current_date.day)
    
    # 飞行时间
    dir_tof_years = st.number_input("飞行时间(年)", min_value=0.1, max_value=20.0, value=2.0, step=0.1)
    
    # 星体选择
    col4, col5 = st.columns(2)
    with col4:
        dir_departure_body = st.selectbox("出发星体", planner.get_planet_list(), index=planner.get_planet_list().index("木星"))
    with col5:
        dir_arrival_body = st.selectbox("到达星体", planner.get_planet_list(), index=planner.get_planet_list().index("海王星"))
    
    # 网格数
    dir_N = st.number_input("网格数", min_value=10, max_value=100, value=30, step=10)
    
    # 优化类型
    optimize_type = st.selectbox("优化类型", ["出发方向", "到达方向", "同时优化"])
    
    # 优化按钮
    if st.button("优化方向"):
        try:
            # 验证输入
            is_valid, message = planner.validate_input(
                dir_start_year, dir_start_month, dir_start_day, dir_tof_years, dir_departure_body, dir_arrival_body
            )
            if not is_valid:
                st.error(message)
            else:
                # 执行优化
                if optimize_type == "出发方向":
                    dep_theta, dep_phi, min_dv = direction_optimizer.optimize_departure_direction(
                        start_year=dir_start_year,
                        start_month=dir_start_month,
                        start_day=dir_start_day,
                        tof_years=dir_tof_years,
                        departure_body=dir_departure_body,
                        arrival_body=dir_arrival_body,
                        N=dir_N
                    )
                    result = f"最优出发方向:\n"
                    result += f"theta: {dep_theta:.4f} rad ({np.degrees(dep_theta):.2f}°)\n"
                    result += f"phi: {dep_phi:.4f} rad ({np.degrees(dep_phi):.2f}°)\n"
                    result += f"最小速度增量: {min_dv:.4f} km/s"
                elif optimize_type == "到达方向":
                    arr_theta, arr_phi, min_dv = direction_optimizer.optimize_arrival_direction(
                        start_year=dir_start_year,
                        start_month=dir_start_month,
                        start_day=dir_start_day,
                        tof_years=dir_tof_years,
                        departure_body=dir_departure_body,
                        arrival_body=dir_arrival_body,
                        N=dir_N
                    )
                    result = f"最优到达方向:\n"
                    result += f"theta: {arr_theta:.4f} rad ({np.degrees(arr_theta):.2f}°)\n"
                    result += f"phi: {arr_phi:.4f} rad ({np.degrees(arr_phi):.2f}°)\n"
                    result += f"最小速度增量: {min_dv:.4f} km/s"
                else:  # 同时优化
                    dep_theta, dep_phi, arr_theta, arr_phi, min_dv = direction_optimizer.optimize_both_directions(
                        start_year=dir_start_year,
                        start_month=dir_start_month,
                        start_day=dir_start_day,
                        tof_years=dir_tof_years,
                        departure_body=dir_departure_body,
                        arrival_body=dir_arrival_body,
                        N=dir_N
                    )
                    result = f"最优出发方向:\n"
                    result += f"theta: {dep_theta:.4f} rad ({np.degrees(dep_theta):.2f}°)\n"
                    result += f"phi: {dep_phi:.4f} rad ({np.degrees(dep_phi):.2f}°)\n\n"
                    result += f"最优到达方向:\n"
                    result += f"theta: {arr_theta:.4f} rad ({np.degrees(arr_theta):.2f}°)\n"
                    result += f"phi: {arr_phi:.4f} rad ({np.degrees(arr_phi):.2f}°)\n\n"
                    result += f"最小速度增量: {min_dv:.4f} km/s"
                
                st.success("方向优化完成")
                st.code(result)
        except Exception as e:
            st.error(f"优化过程中出现错误: {e}")

# 页脚
st.sidebar.markdown("---")
st.sidebar.markdown("太阳系轨道设计工具 v1.0")
st.sidebar.markdown("使用Streamlit实现")
