#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统测试脚本
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.solar_system import SolarSystem
from core.trajectory_optimizer import TrajectoryOptimizer
from core.visualization import Visualization
from features.orbit_planner import OrbitPlanner
from features.constraints import Constraints
from features.porkchop import Porkchop
from features.direction_optimizer import DirectionOptimizer
from utils.config import Config
from utils.data_processor import DataProcessor

class SystemTester:
    """系统测试类"""
    
    def __init__(self):
        """初始化系统测试器"""
        self.test_results = {}
    
    def test_core_modules(self):
        """测试核心模块"""
        print("=== 测试核心模块 ===")
        
        # 测试太阳系模型
        try:
            solar_system = SolarSystem()
            earth_pos = solar_system.calculate_body_position('地球', 2023, 1, 1)
            print("OK 太阳系模型测试通过")
            self.test_results['solar_system'] = True
        except Exception as e:
            print(f"ERROR 太阳系模型测试失败: {e}")
            self.test_results['solar_system'] = False
        
        # 测试轨迹优化器
        try:
            optimizer = TrajectoryOptimizer()
            print("OK 轨迹优化器测试通过")
            self.test_results['trajectory_optimizer'] = True
        except Exception as e:
            print(f"ERROR 轨迹优化器测试失败: {e}")
            self.test_results['trajectory_optimizer'] = False
        
        # 测试可视化引擎
        try:
            viz = Visualization()
            print("OK 可视化引擎测试通过")
            self.test_results['visualization'] = True
        except Exception as e:
            print(f"ERROR 可视化引擎测试失败: {e}")
            self.test_results['visualization'] = False
    
    def test_feature_modules(self):
        """测试功能模块"""
        print("\n=== 测试功能模块 ===")
        
        # 测试轨道规划器
        try:
            planner = OrbitPlanner()
            planets = planner.get_planet_list()
            print("OK 轨道规划器测试通过")
            self.test_results['orbit_planner'] = True
        except Exception as e:
            print(f"ERROR 轨道规划器测试失败: {e}")
            self.test_results['orbit_planner'] = False
        
        # 测试约束处理器
        try:
            constraints = Constraints()
            thrust = constraints.convert_thrust_units(1.0, 'AU/year²', 'km/s²')
            print("OK 约束处理器测试通过")
            self.test_results['constraints'] = True
        except Exception as e:
            print(f"ERROR 约束处理器测试失败: {e}")
            self.test_results['constraints'] = False
        
        # 测试猪排图生成器
        try:
            porkchop = Porkchop()
            print("OK 猪排图生成器测试通过")
            self.test_results['porkchop'] = True
        except Exception as e:
            print(f"ERROR 猪排图生成器测试失败: {e}")
            self.test_results['porkchop'] = False
        
        # 测试方向优化器
        try:
            direction_optimizer = DirectionOptimizer()
            print("OK 方向优化器测试通过")
            self.test_results['direction_optimizer'] = True
        except Exception as e:
            print(f"ERROR 方向优化器测试失败: {e}")
            self.test_results['direction_optimizer'] = False
    
    def test_utils(self):
        """测试工具模块"""
        print("\n=== 测试工具模块 ===")
        
        # 测试配置管理器
        try:
            config = Config()
            mu = config.get('solar_system.mu')
            print("OK 配置管理器测试通过")
            self.test_results['config'] = True
        except Exception as e:
            print(f"ERROR 配置管理器测试失败: {e}")
            self.test_results['config'] = False
        
        # 测试数据处理器
        try:
            data_processor = DataProcessor()
            print("OK 数据处理器测试通过")
            self.test_results['data_processor'] = True
        except Exception as e:
            print(f"ERROR 数据处理器测试失败: {e}")
            self.test_results['data_processor'] = False
    
    def test_integration(self):
        """测试集成功能"""
        print("\n=== 测试集成功能 ===")
        
        # 测试简单轨道规划
        try:
            planner = OrbitPlanner()
            # 验证输入
            is_valid, message = planner.validate_input(
                2300, 6, 1, 2, "木星", "海王星"
            )
            if is_valid:
                print("OK 输入验证测试通过")
                self.test_results['input_validation'] = True
            else:
                print(f"ERROR 输入验证测试失败: {message}")
                self.test_results['input_validation'] = False
        except Exception as e:
            print(f"ERROR 集成测试失败: {e}")
            self.test_results['input_validation'] = False
    
    def generate_report(self):
        """生成测试报告"""
        print("\n=== 系统测试报告 ===")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"测试总数: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {total_tests - passed_tests}")
        print(f"测试通过率: {passed_tests / total_tests * 100:.1f}%")
        
        print("\n详细测试结果:")
        for module, result in self.test_results.items():
            status = "通过" if result else "失败"
            print(f"{module}: {status}")
        
        if passed_tests == total_tests:
            print("\nSUCCESS 所有测试通过！系统运行正常。")
            return True
        else:
            print("\nFAILURE 部分测试失败，需要进一步修复。")
            return False

if __name__ == "__main__":
    """运行系统测试"""
    print("开始系统测试...")
    
    tester = SystemTester()
    tester.test_core_modules()
    tester.test_feature_modules()
    tester.test_utils()
    tester.test_integration()
    
    tester.generate_report()
