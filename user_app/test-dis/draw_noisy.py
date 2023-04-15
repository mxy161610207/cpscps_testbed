import numpy as np
import matplotlib.pyplot as plt

# 定义测量范围和量程误差
x_min, x_max = 0.1, 10
err_range = 0.05

# 定义噪声的均值和标准差
mu = 0
sigma = err_range * np.linspace(x_min, x_max, 100)

# 定义横坐标和纵坐标
x = np.linspace(x_min, x_max, 100)
y_true = x
y_noise = np.random.normal(mu, sigma)

# 绘制红色曲线，表示测量值和真实值的关系
plt.plot(x, y_true, color='red', label='True Distance')

# 绘制蓝色曲线，表示测量值和噪声的关系
plt.plot(x, y_noise, color='blue', label='Measurement Noise')

# 设置图例、坐标轴标签和标题
plt.legend()
plt.xlabel('Measured Distance (m)')
plt.ylabel('Distance (m)')
plt.title('Measurement Error Distribution')

# 显示图像
plt.show()
