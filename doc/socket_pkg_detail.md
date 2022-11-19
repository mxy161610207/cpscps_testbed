本周文档用于描述不同模块间socket通信的数据包格式。

---

## Manager 管理的多进程数据

```python
# 系统多进程资源
platform_manager = Manager()    

platform_status_resources = {}
platform_message_resources = {}
platform_socket_address = {
    'phy_sender': ('127.0.0.1', 41997),
    'sdk' : ('127.0.0.1', 41011),
    'location': ('127.0.0.1', 41234),
}

# --- 定位系统工具 ---
platform_status_resources['location'] = Value('i',0)
platform_message_resources['location'] = Queue(-1)
platform_message_resources['grd_position'] = platform_manager.dict()
platform_message_resources['sim_position'] = platform_manager.dict()

# --- SDK通信工具 ---
platform_status_resources['sdk'] = Value('i',0)
platform_message_resources['sdk'] = Queue(-1)


# use ---------------------------
# 1)
physical_sender_addr = platform_socket_address['phy_sender']
location_server_addr = platform_socket_address['location']

# 3) sdk
sdk_platform_status = platform_status_resources['sdk']
sdk_platform_message = platform_message_resources['sdk']

# simluate_sender_addr = platform_socket_address['sdk']

```



显示syncer格式

```python
{
	'x': pos_x,
    'y': pos_y,
    'deg' : pos_deg,
    'rad' : pos_rad,
    'status': ActionAnalysis.TYPE.name
    'info': information
}
```





---





## 平台模块status值说明

### location_server_status

```python
platform_status_resources['location'] = Value('i',0)	
location_server_status = platform_status_resources['location']
```

| .value == ? | 说明     | 动作              |      |
| ----------- | -------- | ----------------- | ---- |
| 0           | 无服务器 | raiser 创建服务器 |      |
| 1           | 正常工作 | 无                |      |
| 2           | 重启中   | 无                |      |
| 3           | 关闭中   | 无                |      |



### sdk_platform_status 小车平台状态

```python
platform_status_resources['sdk'] = Value('i',0)	
sdk_platform_status = platform_status_resources['sdk']
```

| .value == ? | 说明         | 动作                          |      |
| ----------- | ------------ | ----------------------------- | ---- |
| 0           | 无小车连接   | 连接EP小车                    |      |
| 1           | 小车未初始化 | 接受DJI动作，并初始化小车定位 |      |
| 2           | 平台空闲     | 等待用户API调用，USER         |      |
| 3           | 平台忙碌     | 挂起                          |      |

---



## Location Module 格式说明

### 数据包来源

该模块之间采用socket通信：

- 发送格式： 编码后的json字符串 loads/dumps

1. 定位模块 Location Module
   - 地址：`('127.0.0.1', 41234)`， 标记`location`
   - 模式：收发

2. SDK物理端：Physical Message Sender
   - 地址：`('127.0.0.1', 41011)`, 标记`phy_sender`
   - 格式：收、发

### 相关文件

- location_server.py： socket的收发端口
  - 收：将json格式数据包添加到队列`self.calculater.info_queue`中
  - 发：一些数据包需要reply，从`self._send_msg_queue`中取出需要发送的包

### 格式说明

```json
// 接收json格式：
{
    'term_id': 9999,  			// 0-9999 
    'tpye': PACKAGE_TYPE, 		//
    'info': {					// 一个json格式的数据包
        PACKAGE_INFO_JSON	
    }
}
```

| PACKAGE_TYPE | PACKAGE_INFO_JSON                                            | 是否回复 | 说明                                                  |
| ------------ | ------------------------------------------------------------ | -------- | ----------------------------------------------------- |
| SYSTEM_TYPE  | 'next_state': SystemState.TYPE                               | No       | 系统状态                                              |
| ACTION_TYPE  | 'api' : 'move',<br>'x':proto._x_spd,<br>'y':proto._y_spd,<br>'z':proto._z_spd,<br>'spd_xy':3,<br>'spd_z':3, | No       | SDK运行的动作指令<br>用于推断小车的定位               |
| ANGLE_TYPE   | 'angle':   d-self.angle_init_val,<br>'raw_angle': d          | No       | 角度<br>'angle'相对角度<br>'raw_angle':上电后当前角度 |
| SENSOR_TYPE  | 'sensor_info':[F,B,L,R],<br>'need_location':stop_tag         | stop_tag | stop_tag = true时回复<br>返回当前测距组的定位结果     |
| QUERY        | 'query_type':'position'                                      | Yes      | 定位查询<br>返回静止后小车的定位                      |
| SYNC         | 'status': 'init'  / 'sync',<br>'sync_code': random.randint(0,10000) | Yes      | 系统状态同步                                          |
| EOF          | 空                                                           |          |                                                       |

```json
// 发送json格式：
{
    'query_id': qid,		// 询问数据包的term_id
    'type': REPLY_TYPE,
    'info': {
        REPLY_INFO
    }
}
```

| REPLY_TYPE | REPLY_INFO                                                   | 说明                                   |
| ---------- | ------------------------------------------------------------ | -------------------------------------- |
| position   | 'location_analysis': location_analysis.name,<br>'x': pos.x,<br>'y': pos.x,<br>'deg': pos.deg | 对QUERY的回复                          |
| snapshot   | 'location_analysis': location_analysis.name,<br/>'x': pos.x,<br/>'y': pos.x,<br/>'deg': pos.deg | 对SENSOR_TYPE中<br>stop_tag=True的回复 |
| sync       | 'sync_code':sync_code                                        | 对SYNC的回复<br>用来测时延             |

---

## SDK 动作 格式说明

### sdk_platform_message 数据包来源

该模块之间采用`mulitprocess.Queue`通信：

- 存储格式： 编码后的json字符串 loads/dumps

- 变量定义: `manager.py`

```python
platform_message_resources['sdk'] = Queue(-1)	//sdk_platform_message
```

- 获取和操作get: `sdk_handler.py`

```json
// 读取json格式：
{
    'tpye': PACKAGE_TYPE, 		//
    'info': {					// 一个json格式的数据包
        PACKAGE_INFO_JSON	
    }
}
```

| PACKAGE_TYPE  | PACKAGE_INFO_JSON                                   | 操作                                                         | 说明          |
| ------------- | --------------------------------------------------- | ------------------------------------------------------------ | ------------- |
| SYSTEM_STATUS | 'status': 'init_success' / 'shutdown'               | 'init_success':<br>小车初始化成功,平台状态切换<br>'shutdown'：<br/>和小车断连 | 系统状态      |
| ACTION        | 'api_version': 'DJI'/'USER'<br>'api_info': API_INFO |                                                              | 动作执行类API |
| SENSOR        | 'sensor_module': 'ir_sensor'                        |                                                              | 感知类API     |



- put()

1. 定位模块 Location Module
   - 地址：`('127.0.0.1', 41234)`， 标记`location`
   - 模式：收发

2. SDK物理端：Physical Message Sender
   - 地址：`('127.0.0.1', 41011)`, 标记`sdk`
   - 格式：收、发