【该目录中，`test-*`的文件都是杂项文件，用于辅助我的论文绘图和debug，可以忽略】

本目录是为[上下文服务平台](https://gitee.com/Crabor/frame/tree/dev/)编写的APP注册服务。



APP->ContextPlatform->Driver

| APP中语句                                                    | 传输的数据                                                   | 解释                                              |
| ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------- |
| ep_chassis.move(x,y,z,xy_spd,z_spd).wait_for_completed(timeout) | SAFE: chassis move x {x} y {y} z {z} vxy {xy_spd} vz{z_spd} timeout {timeout}; | x{0.1} 代表前进0.1米；timeout=-1即APP中设置为None |
| ep_chassis.drive_speed(x_spd,y_spd,z_spd)                    | SAFE: chassis speed x {x} y {y} z {z} timeout {timeout};     |                                                   |
|                                                              |                                                              |                                                   |



Driver->ContextPlatform->APP

每隔0.5秒

```
{
  "ir_distance": {
    "F": 2762,
    "R": 1076,
    "B": 875,
    "L": 1133
  },
  "chassis_status": 0、1、2、-1
}
```

