# Ingress 多重控制场规划器

基于地图上的Portal点，计算最优化的连接方式和最短路径，用于最大化AP（行动点数）收益。

## 功能特性

- 🎯 **最优连接规划**：使用Delaunay三角剖分和优化算法找到最大AP收益的连接方案
- 📍 **Portal管理**：支持从经纬度坐标读取和导入Portal位置
- 🚶 **路径优化**：计算连接方案的最短行走路径
- 👥 **多人规划**：支持多人协作，自动分配任务和AP
- 📊 **结果可视化**：生成连接方案和路径的可视化结果（支持Matplotlib和Manim动画）
- 🎬 **动画演示**：使用Manim创建精美的连接动画，直观展示规划过程

## Ingress多重控制场规则

1. 所有link必须形成有效的三角形（field）
2. 同一个三角形内最多只能有8个点
3. link不能相交（除非在portal处）
4. 最大化AP收益：每个link和field都有对应的AP值

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本使用

```python
from planner import IngressPlanner

# 创建规划器
planner = IngressPlanner()

# 添加Portal点（经纬度坐标）
portals = [
    (40.008008, 116.327477),  # Portal 1
    (40.008102, 116.326605),  # Portal 2
    # ... 更多portal
]

# 生成最优连接方案
solution = planner.plan(portals)

# 输出结果
print(f"总AP: {solution.total_ap}")
print(f"行走距离: {solution.distance} km")
```

### 从文件导入Portal

```bash
python planner.py --input portals.txt --output solution.txt
```

### 可视化结果

#### 使用Matplotlib（静态图像）

```bash
# 生成静态图像
python visualize.py --input portals.txt --output result.png

# 多人规划可视化
python visualize.py --input portals.txt --output result.png --agents 3
```

#### 使用Manim（动画视频）

```bash
# 生成动画视频（需要先安装Manim）
manim -pql ingress_scene.py IngressScene

# 使用自定义Portal文件（需要修改ingress_scene.py中的CONFIG）
# 或使用命令行参数（需要修改代码支持）

# 多人规划动画
manim -pql ingress_scene.py MultiAgentScene
```

### 多人规划

```python
# 3人协作规划
solution = planner.multi_agent_plan(portals, num_agents=3)
for i, agent_plan in enumerate(solution.agent_plans):
    print(f"Agent {i}: {agent_plan.ap} AP, {agent_plan.distance} km")
```

## 输入格式

Portal坐标文件格式（portals.txt）：
```
40.008008,116.327477
40.008102,116.326605
40.008034,116.325578
...
```

或使用命名格式：
```
Portal1,40.008008,116.327477
Portal2,40.008102,116.326605
...
```

## 获取Portal坐标

### 方式一：交互式地图选择（推荐）🗺️

**使用Folium地图工具：**
```bash
# 创建交互式地图，点击选择Portal
python map_selector.py --center-lat 40.008 --center-lon 116.327
```

**使用Web界面（更强大）：**
```bash
# 启动Web服务器
python web_map_selector.py
# 在浏览器中打开 http://localhost:5000
```

Web界面功能：
- ✅ 点击地图添加Portal
- ✅ 拖拽标记调整位置
- ✅ 从文件加载/导出
- ✅ 从Ingress Intel URL获取Portal
- ✅ 多种地图图层切换

### 方式二：从Ingress Intel获取📍

**浏览器脚本（最简单）：**
1. 打开 [Ingress Intel](https://intel.ingress.com/intel) 并登录
2. 导航到目标区域
3. 按F12打开控制台
4. 复制并执行 `browser_extract.js` 中的代码
5. 自动下载Portal数据文件

**命令行工具：**
```bash
# 从Intel URL获取
python ingress_api.py --url "https://intel.ingress.com/intel?ll=40.008,116.327&z=15"

# 从指定区域获取
python ingress_api.py --area 40.010 40.006 116.330 116.324
```

详细说明请查看 [MAP_GUIDE.md](MAP_GUIDE.md)

## 输出格式

输出包含：
- 连接方案（link列表）
- 每个link的AP值
- 总AP值
- 行走距离
- 路径顺序

## 算法说明

本项目参考了以下算法和策略：

1. **Delaunay三角剖分**：用于生成可行的三角形连接
2. **贪心优化**：在可行连接中选择最优方案
3. **聚类分析**：用于多人任务分配

## 参考资料

- [Ingress Intel](https://intel.ingress.com/intel)
- [multi-field项目](https://github.com/Nuullll/multi-field)
- [maxfield项目](https://github.com/jpeterbaker/maxfield)
- [多重控制场原理](https://zhuanlan.zhihu.com/p/19579305)

## 许可证

MIT License

