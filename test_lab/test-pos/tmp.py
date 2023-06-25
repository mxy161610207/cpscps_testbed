import matplotlib.pyplot as plt
from matplotlib.colorbar import ColorbarBase

# 定义单元格状态
cell_state = [
    [0, 0, 3, 0],
    [0, 0, 2, 0],
    [0, 1, 1, 0],
    [1, 1, 0, 0]]

# 设置颜色映射
cmap = plt.cm.colors.ListedColormap(
    # 0白 1黄 2绿 3蓝 4灰色
    [(1, 1, 1, 0), (1, 1, 0, 0.5), (0, 1, 0, 0.5), (0, 0, 1, 0.5), (0.5, 0.5, 0.5, 0.5)])

# 定义每个单元格的边长
cell_size = 20

# 绘制正方形
for i in range(len(cell_state)):
    for j in range(len(cell_state[i])):
        x = j * cell_size
        y = i * cell_size
        cell_color = cmap(cell_state[3-i][j])
        rect = plt.Rectangle((x, y), cell_size, cell_size, facecolor=cell_color, edgecolor='white')
        plt.gca().add_patch(rect)

# 绘制颜色映射图例
bounds = [0, 1, 2, 3, 4]
norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

fig, ax = plt.subplots(figsize=(0.5, 5))
cbar = ColorbarBase(ax, cmap=cmap, norm=norm, boundaries=bounds, ticks=bounds)
cbar.ax.set_yticklabels(['White', 'Yellow', 'Green', 'Blue', 'Gray'], fontsize=10)

plt.xlim([0, len(cell_state)*cell_size])
plt.ylim([0, len(cell_state)*cell_size])
plt.axis('equal')
plt.axis('off')
plt.show()
