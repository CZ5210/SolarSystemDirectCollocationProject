import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import mplcursors

# 生成数据（保留数据副本，以便在回调中引用）
np.random.seed(42)
n = 50
x = np.random.rand(n)
y = np.random.rand(n)
z = np.random.rand(n)

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
sc = ax.scatter(x, y, z, c='r', marker='o')

cursor = mplcursors.cursor(sc, hover=True)

@cursor.connect("add")
def on_add(sel):
    # 使用 sel.index 获取被选中点在数据数组中的索引
    idx = sel.index
    # 从原始数据中获取该点的 x, y, z
    x_val = x[idx]
    y_val = y[idx]
    z_val = z[idx]
    # 设置标注文本
    sel.annotation.set_text(f'x: {x_val:.2f}\ny: {y_val:.2f}\nz: {z_val:.2f}')
    sel.annotation.get_bbox_patch().set(fc="lightyellow", ec="black", alpha=0.8)

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
plt.title('3D Scatter Plot with mplcursors (workaround)')
plt.show()