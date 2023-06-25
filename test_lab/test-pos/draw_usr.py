import matplotlib.pyplot as plt
from matplotlib.colorbar import ColorbarBase

# 定义单元格状态
cell_state = [
    [0, 3, 2, 3],
    [0, 0, 1, 0],
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

def draw_maze(edge_len):
    # 读入迷宫信息
    with open('maze.txt', 'r') as f:
        M,W,H = map(int, f.readline().split())
        walls = []
        for _ in range(M):
            x1, y1, x2, y2 = map(int, f.readline().split())
            walls.append((x1, y1, x2, y2))
    
    global plt    
    for x1, y1, x2, y2 in walls:
        plt.plot([x1*edge_len, x2*edge_len], [y1*edge_len, y2*edge_len], color='black')

draw_maze(cell_size)

# # 绘制颜色映射图例
# bounds = [0, 1, 2, 3, 4]
# norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)
# fig, ax = plt.subplots()
# plt.colorbar(ColorbarBase(ax, cmap=cmap, norm=norm, boundaries=bounds, ticks=bounds))


plt.xlim([0, len(cell_state)*cell_size])
plt.ylim([0, len(cell_state)*cell_size])
plt.axis('equal')
plt.axis('off')
plt.show()


