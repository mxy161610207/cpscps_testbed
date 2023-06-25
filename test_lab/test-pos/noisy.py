import random

random.seed()

x = [2099, 1257, 1302, 243]
errors = []
int_errors = []
for i in range(len(x)):
    sigma = 0.05 * x[i]
    error = random.gauss(0, sigma)
    errors.append(error)
    int_errors.append(round(error))
    x[i] += int_errors[i]
    
print("加上误差后的数据为：", x)
print("误差列表为：", errors)
print("误差列表为：", int_errors)
