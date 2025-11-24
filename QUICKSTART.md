# 快速开始指南

## 安装

```bash
# 安装依赖
pip install -r requirements.txt
```

## 基本使用

### 1. 准备Portal坐标文件

创建文本文件 `my_portals.txt`，格式如下：

```
Portal1,40.008008,116.327477
Portal2,40.008102,116.326605
Portal3,40.008034,116.325578
```

或者简单的经纬度格式：

```
40.008008,116.327477
40.008102,116.326605
40.008034,116.325578
```

### 2. 生成连接方案

```bash
# 基本规划
python planner.py --input my_portals.txt --output solution.txt

# 3人协作规划
python planner.py --input my_portals.txt --output solution.txt --agents 3
```

### 3. 可视化结果

#### 使用Matplotlib（静态图像）

```bash
# 可视化单人方案
python visualize.py --input my_portals.txt --output result.png

# 可视化多人方案
python visualize.py --input my_portals.txt --output result.png --agents 3
```

#### 使用Manim（动画视频）🎬

Manim可以创建精美的动画演示，展示连接过程：

```bash
# 1. 修改ingress_scene.py中的CONFIG，设置input_file为你的portal文件
#    或者直接使用示例数据

# 2. 生成低质量预览（快速）
manim -pql ingress_scene.py IngressScene

# 3. 生成高质量视频
manim -pqh ingress_scene.py IngressScene

# 4. 多人规划动画
manim -pql ingress_scene.py MultiAgentScene
```

**Manim参数说明：**
- `-p`: 渲染后自动播放
- `-q`: 质量等级（l=low, m=medium, h=high）
- `-l`: 低质量（快速预览）
- `-m`: 中等质量
- `-h`: 高质量（最终输出）

**Manim动画特点：**
- ✨ 逐步显示Portal点
- 🔗 动态创建Link连接
- 📐 填充Field区域
- 🚶 动画展示行走路径
- 🎨 精美的视觉效果和过渡动画

## 使用Python API

```python
from planner import IngressPlanner

# 创建规划器
planner = IngressPlanner()

# 方式1: 从文件加载
planner.load_portals_from_file('portals_zijing.txt')

# 方式2: 直接添加Portal
planner.add_portal(40.008008, 116.327477, "Portal1")
planner.add_portal(40.008102, 116.326605, "Portal2")

# 生成方案
solution = planner.plan()

# 查看结果
print(f"总AP: {solution.total_ap}")
print(f"Link数量: {len(solution.links)}")
print(f"Field数量: {len(solution.fields)}")
print(f"行走距离: {solution.distance/1000:.2f} km")

# 多人规划
multi_solution = planner.multi_agent_plan(num_agents=3)
for i, agent_plan in enumerate(multi_solution.agent_plans):
    print(f"Agent {i}: {agent_plan.ap} AP")
```

## 获取Portal坐标

### 方式一：交互式地图选择

**使用Web界面（推荐）：**
```bash
# 启动Web服务器
python web_map_selector.py

# 在浏览器中打开 http://localhost:5000
# 点击地图添加Portal，或从Ingress获取
```

**使用Folium地图：**
```bash
python map_selector.py --center-lat 40.008 --center-lon 116.327
```

### 方式二：从Ingress获取

**浏览器脚本（最简单）：**
1. 打开 https://intel.ingress.com/intel 并登录
2. 按F12打开控制台
3. 执行 `browser_extract.js` 中的代码
4. 自动下载Portal数据

**命令行：**
```bash
python ingress_api.py --url "https://intel.ingress.com/intel?ll=40.008,116.327&z=15"
```

详细说明请查看 [MAP_GUIDE.md](MAP_GUIDE.md)

## 测试

运行测试脚本：

```bash
python test_planner.py
```

## 示例数据

项目包含两个示例数据文件：

- `example_portals.txt`: 简单示例（5个portal）
- `portals_zijing.txt`: 紫荆雕塑园数据（22个portal）

运行示例：

```bash
# 使用示例数据
python planner.py --input example_portals.txt

# 使用紫荆雕塑园数据（参考multi-field项目）
python planner.py --input portals_zijing.txt --output zijing_solution.txt
```

## 输出说明

输出包含以下信息：

1. **总AP**: 所有link和field的总行动点数
2. **Link数量**: 连接的link总数
3. **Field数量**: 形成的field（三角形）总数
4. **行走距离**: 按连接顺序行走的总距离（公里）
5. **连接方案**: 每条link的详细坐标

## 注意事项

1. Portal坐标使用经纬度格式（度）
2. 确保至少有3个Portal才能形成field
3. 算法会避免link相交（除非在portal处）
4. 每个三角形内最多包含8个其他portal点

## 常见问题

**Q: 为什么结果为空？**
A: 确保至少提供了3个Portal坐标，且它们之间可以形成有效的三角形。

**Q: 如何获取Ingress Portal坐标？**
A: 可以从Ingress Intel地图 (https://intel.ingress.com/intel) 获取Portal的经纬度坐标。

**Q: 行走距离计算准确吗？**
A: 使用geodesic距离计算，考虑地球曲率，对于小范围区域（<10km）误差很小。

**Q: 如何优化结果？**
A: 算法使用贪心策略，对于大规模问题可以考虑多次运行并选择最优结果。

