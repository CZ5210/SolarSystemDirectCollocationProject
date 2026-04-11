import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm, colors
from scipy.interpolate import griddata
import seaborn as sns

class Porkchop:
    """猪排图生成类"""
    
    def __init__(self):
        """初始化猪排图生成器"""
        pass
    
    def plot_porkchop_departure_tof(self, csv_path='porkchop_results.csv', 
                                   save_path='porkchop_dep_tof.png'):
        """
        绘制以出发时间为横轴、飞行时间为纵轴的猪排图（Seaborn热力图版）
        
        :param csv_path: 猪排图结果CSV文件路径
        :param save_path: 生成图表的保存路径
        :return: None
        """
        # 1. 读取并解析CSV数据
        print(f"正在读取数据文件: {csv_path}")
        df = pd.read_csv(csv_path, index_col=0)
        
        # 解析出发年份（行索引）
        departure_years = df.index.astype(int).to_numpy()
        
        # 解析飞行时间（列名）
        tof_years = np.array([float(col.strip('y')) for col in df.columns])
        
        print(f"出发年份: {departure_years.tolist()}")
        print(f"飞行时间: {tof_years.tolist()}")
        
        # 2. 直接使用原始数据框，无需重新计算到达年份
        # 创建用于热力图的数据框
        plot_df = pd.DataFrame({
            '出发年份': np.repeat(departure_years, len(tof_years)),
            '飞行时间': np.tile(tof_years, len(departure_years)),
            'ΔV (km/s)': df.values.flatten()
        })
        
        # 移除NaN值
        plot_df = plot_df.dropna(subset=['ΔV (km/s)'])
        
        print(f"有效数据点数量: {len(plot_df)}")
        print(f"ΔV范围: [{plot_df['ΔV (km/s)'].min():.2f}, {plot_df['ΔV (km/s)'].max():.2f}] km/s")
        
        # 3. 创建透视表（出发年份 vs 飞行时间）
        pivot_table = plot_df.pivot_table(
            index='飞行时间', 
            columns='出发年份', 
            values='ΔV (km/s)'
        )
        
        # 排序（飞行时间从小到大）
        pivot_table = pivot_table.sort_index(axis=0)
        
        print(f"透视表形状: {pivot_table.shape}")
        print(f"行索引（飞行时间）: {pivot_table.index.tolist()}")
        print(f"列（出发年份）: {pivot_table.columns.tolist()}")
        
        # 4. 创建图表
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 根据数据量调整图表大小
        n_rows = len(pivot_table.index)
        n_cols = len(pivot_table.columns)
        fig_height = max(8, n_rows * 0.8)  # 每行0.8英寸
        fig_width = max(12, n_cols * 0.8)  # 每列0.8英寸
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height))
        
        # 选择颜色映射
        cmap = sns.color_palette("viridis", as_cmap=True)
        
        # 计算颜色范围
        dv_min = plot_df['ΔV (km/s)'].min()
        dv_max = plot_df['ΔV (km/s)'].max()
        
        # 5. 绘制Seaborn热力图
        heatmap = sns.heatmap(
            pivot_table,
            ax=ax,
            cmap=cmap,
            annot=True,                # 显示数值
            fmt='.1f',                # 数值格式（1位小数）
            annot_kws={'size': 10},   # 标注字体大小
            linewidths=1,             # 格子边框宽度
            linecolor='white',        # 格子边框颜色
            cbar=True,                # 显示颜色条
            cbar_kws={
                'label': '速度增量 ΔV (km/s)',
                'shrink': 0.8,
                'pad': 0.02
            },
            vmin=dv_min,
            vmax=dv_max,
            cbar_ax=None,
            xticklabels=True,
            yticklabels=True,
            alpha=0.9
        )
        
        # 6. 关键调整：纵轴从小到大（从下到上）
        ax.invert_yaxis()
        
        # 7. 美化图表
        # 设置标题和坐标轴标签
        ax.set_title('发射窗口分析猪排图',
                     fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('出发年份 (年)', fontsize=14, fontweight='bold')
        ax.set_ylabel('飞行时间 (年)', fontsize=14, fontweight='bold')
        
        # 调整X轴刻度标签（出发年份）
        if len(pivot_table.columns) > 0:
            xtick_labels = [str(int(col)) for col in pivot_table.columns]
            ax.set_xticklabels(xtick_labels, rotation=45, ha='right', fontsize=11)
        
        # 调整Y轴刻度标签（飞行时间）
        if len(pivot_table.index) > 0:
            # 飞行时间可能是小数（如1.5年），显示1位小数
            ytick_labels = [f'{idx:.1f}' if idx % 1 != 0 else f'{int(idx)}' 
                           for idx in pivot_table.index]
            ax.set_yticklabels(ytick_labels, fontsize=11)
        
        # 调整颜色条
        cbar = heatmap.collections[0].colorbar
        cbar.set_label('速度增量 ΔV (km/s)', fontsize=12, fontweight='bold')
        cbar.ax.tick_params(labelsize=10)
        
        # 添加背景网格
        ax.set_axisbelow(True)
        ax.grid(True, which='major', color='gray', linestyle='-', linewidth=0.5, alpha=0.2)
        
        # 9. 调整布局
        plt.tight_layout()
        
        # 10. 保存图表
        plt.savefig(save_path, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"\n图表已保存至: {save_path}")
        
        # 11. 显示图表
        plt.show()
    
    def plot_porkchop_contour(self, csv_path='porkchop_results.csv', 
                             save_path='porkchop_contour.png',
                             custom_levels=None):
        """
        绘制等高线版的猪排图（更专业美观）- 飞行时间为Y轴
        
        :param csv_path: 猪排图结果CSV文件路径
        :param save_path: 生成图表的保存路径
        :param custom_levels: 自定义的等高线级别参数
        :return: None
        """
        # 1. 读取并解析CSV数据
        print(f"正在读取数据文件: {csv_path}")
        df = pd.read_csv(csv_path, index_col=0)
        
        # 解析出发年份（行索引）
        departure_years = df.index.astype(float).to_numpy()
        
        # 解析飞行时间（列名）
        tof_years = np.array([float(col.strip('y')) for col in df.columns])
        
        print(f"出发年份范围: {departure_years.min()} - {departure_years.max()}")
        print(f"飞行时间范围: {tof_years.min()} - {tof_years.max()} 年")
        
        # 准备数据容器 - 现在Y轴是飞行时间
        X_dep = []  # 出发年份
        Y_tof = []  # 飞行时间
        Z_dv = []   # ΔV值
        
        # 构建网格数据
        for i, dep_year in enumerate(departure_years):
            for j, tof in enumerate(tof_years):
                dv = df.iloc[i, j]
                if not np.isnan(dv):
                    X_dep.append(dep_year)
                    Y_tof.append(tof)  # 飞行时间作为Y轴
                    Z_dv.append(dv)
        
        # 转换为numpy数组
        X = np.array(X_dep)
        Y = np.array(Y_tof)
        Z = np.array(Z_dv)
        
        print(f"数据点数量: {len(X)}")
        print(f"ΔV范围: [{Z.min():.2f}, {Z.max():.2f}] km/s")
        
        # 2. 创建规则网格用于等高线
        xi = np.linspace(X.min(), X.max(), 100)
        yi = np.linspace(Y.min(), Y.max(), 100)
        xi_grid, yi_grid = np.meshgrid(xi, yi)
        
        # 使用线性插值填充网格
        zi_grid = griddata((X, Y), Z, (xi_grid, yi_grid), method='linear', fill_value=np.nan)
        
        # 3. 创建图表
        fig, ax = plt.subplots(figsize=(14, 10))
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 4. 创建颜色映射和归一化
        cmap = cm.get_cmap('viridis')
        
        # 根据数据范围设置归一化（兼容自定义级别）
        if custom_levels is not None:
            # 如果有自定义级别，归一化范围用自定义级别的最小/最大值
            vmin = np.min(custom_levels)
            vmax = np.max(custom_levels)
            levels = np.array(custom_levels)
            print(f"使用自定义等高线级别: {levels}")
        else:
            # 原逻辑：基于分位数生成15个级别
            vmin = np.percentile(Z, 5)  # 5%分位数
            vmax = np.percentile(Z, 95)  # 95%分位数
            levels = np.linspace(vmin, vmax, 15)  # 15个等高线级别
            print(f"使用自动生成的等高线级别（15个）: [{vmin:.2f}, {vmax:.2f}]")
        
        norm = colors.Normalize(vmin=vmin, vmax=vmax)
        
        # 5. 绘制等高线填充图
        # 等高线填充（使用统一的levels）
        contourf = ax.contourf(
            xi_grid, yi_grid, zi_grid,
            levels=levels,
            cmap=cmap,
            norm=norm,
            alpha=0.85,
            extend='both'
        )
        
        # 绘制等高线（可以自定义隔几个级别画一条线，比如levels[::2]隔一个画一个）
        contour_lines = ax.contour(
            xi_grid, yi_grid, zi_grid,
            levels=levels,  # 改用全部自定义级别（也可以改成levels[::2]隔一个画）
            colors='black',
            linewidths=0.8,
            alpha=0.6,
            linestyles='-'
        )
        
        # 添加等高线标签（ΔV数值）
        ax.clabel(
            contour_lines,
            inline=True,
            fontsize=9,
            fmt='%1.1f',
            colors='black',
            inline_spacing=5
        )
        
        # 7. 添加颜色条
        cbar = plt.colorbar(contourf, ax=ax, shrink=0.8, pad=0.02)
        cbar.set_label('速度增量 ΔV (km/s)', fontsize=12, fontweight='bold')
        cbar.ax.tick_params(labelsize=10)
        cbar.add_lines(contour_lines)  # 将等高线添加到颜色条
        
        # 8. 设置坐标轴和刻度
        ax.set_xlabel('出发年份 (年)', fontsize=14, fontweight='bold')
        ax.set_ylabel('飞行时间 (年)', fontsize=14, fontweight='bold')
        ax.set_title('发射窗口分析猪排图', 
                     fontsize=16, fontweight='bold', pad=20)
        
        # 设置主要刻度
        # X轴：出发年份
        x_ticks = np.arange(np.floor(X.min()), np.ceil(X.max()) + 1)
        ax.set_xticks(x_ticks)
        ax.set_xticklabels([str(int(x)) for x in x_ticks], rotation=45)
        
        # Y轴：飞行时间
        y_ticks = np.arange(np.floor(Y.min()), np.ceil(Y.max()) + 1)
        ax.set_yticks(y_ticks)
        ax.set_yticklabels([str(int(y)) for y in y_ticks])
        
        # 设置坐标轴范围
        ax.set_xlim([X.min() - 0.5, X.max() + 0.5])
        ax.set_ylim([Y.min() - 0.2, Y.max() + 0.2])
        
        # 9. 添加网格
        ax.grid(True, which='major', alpha=0.2, linestyle='--', linewidth=0.5)
        
        # 11. 优化布局
        plt.tight_layout()
        
        # 12. 保存图像
        plt.savefig(
            save_path,
            dpi=300,
            facecolor='white',
            edgecolor='none',
            bbox_inches='tight',
            pad_inches=0.1
        )
        print(f"\n图表已保存至: {save_path}")
        
        # 13. 显示图表
        plt.show()

if __name__ == "__main__":
    """
    猪排图生成模块测试
    """
    print("===== 测试猪排图生成功能 =====")
    
    # 创建猪排图生成器实例
    porkchop = Porkchop()
    
    # 测试1：绘制热力图版猪排图
    print("\n测试1：绘制热力图版猪排图")
    porkchop.plot_porkchop_departure_tof(
        csv_path='porkchop_results.csv',
        save_path='porkchop_heatmap.png'
    )
    
    # 测试2：绘制等高线版猪排图
    print("\n测试2：绘制等高线版猪排图")
    porkchop.plot_porkchop_contour(
        csv_path='porkchop_results.csv',
        save_path='porkchop_contour.png'
    )
