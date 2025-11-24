# 功能使用总结

本文档总结Ingress规划器的所有功能和使用方法。

## 🚀 快速开始

### 1. 获取Portal坐标

#### 方式A：交互式地图选择（最简单）

```bash
# 启动Web界面
python web_map_selector.py
# 浏览器打开 http://localhost:5000
# 点击地图添加Portal
```

#### 方式B：从Ingress Intel获取（批量）

1. 打开 https://intel.ingress.com/intel
2. 登录后导航到目标区域
3. 按F12打开控制台
4. 执行 `browser_extract.js` 代码
5. 自动下载Portal数据

### 2. 生成连接方案

```bash
python planner.py --input portals.txt --output solution.txt
```

### 3. 可视化结果

```bash
# 静态图像
python visualize.py --input portals.txt --output result.png

# 动画视频
manim -pql ingress_scene.py IngressScene
```

## 📁 文件说明

### 核心功能
- **planner.py** - 核心规划器，生成最优连接方案
- **visualize.py** - Matplotlib静态可视化
- **ingress_scene.py** - Manim动画可视化

### Portal获取工具
- **web_map_selector.py** - Web界面地图选择器（推荐）
- **map_selector.py** - Folium交互式地图工具
- **ingress_api.py** - Ingress Intel API工具
- **browser_extract.js** - 浏览器脚本（从Intel提取）

### 文档
- **README.md** - 项目总览
- **QUICKSTART.md** - 快速开始指南
- **MAP_GUIDE.md** - 地图工具详细说明
- **MANIM_GUIDE.md** - Manim动画指南

## 🎯 完整工作流程示例

### 场景：规划一个新的多重控制场

#### 步骤1：获取Portal
```bash
# 方式1：使用Web界面手动选择
python web_map_selector.py

# 方式2：从Ingress获取
# 在浏览器中使用 browser_extract.js
```

#### 步骤2：生成方案
```bash
python planner.py --input portals.txt --output solution.txt --agents 3
```

#### 步骤3：查看结果
```bash
# 查看文本输出
cat solution.txt

# 生成可视化
python visualize.py --input portals.txt --output result.png

# 生成动画
manim -pql ingress_scene.py IngressScene
```

## 🛠️ 工具对比

| 需求 | 推荐工具 | 命令 |
|------|---------|------|
| 手动选择少量Portal | Web界面 | `python web_map_selector.py` |
| 批量获取Portal | 浏览器脚本 | 执行 `browser_extract.js` |
| 快速预览方案 | 静态图像 | `python visualize.py` |
| 精美演示动画 | Manim动画 | `manim -pql ingress_scene.py IngressScene` |
| 多人规划 | 规划器 | `python planner.py --agents 3` |

## 📚 详细文档索引

- **入门指南**: [QUICKSTART.md](QUICKSTART.md)
- **地图工具**: [MAP_GUIDE.md](MAP_GUIDE.md) ⭐ 新增
- **动画制作**: [MANIM_GUIDE.md](MANIM_GUIDE.md)
- **API文档**: 查看各Python文件的docstring

## 💡 常见问题

### Q: 哪个工具最适合我？

A: 
- **少量Portal（<10个）**: 使用Web界面手动选择
- **大量Portal（>10个）**: 使用浏览器脚本从Ingress获取
- **需要精确位置**: 使用Web界面+卫星图

### Q: 如何快速测试？

A:
```bash
# 使用示例数据
python planner.py --input example_portals.txt
python visualize.py --input example_portals.txt
```

### Q: 支持哪些Portal数据格式？

A:
- TXT格式：`name,lat,lon` 或 `lat,lon`
- JSON格式：`{"name": "...", "lat": ..., "lon": ...}`

### Q: 可以在手机上使用吗？

A:
- Web界面支持手机浏览器
- 在同一WiFi网络下，用手机IP访问服务器

## 🔗 相关链接

- [Ingress Intel地图](https://intel.ingress.com/intel)
- [Ingress官网](https://www.ingress.com/)
- [multi-field项目](https://github.com/Nuullll/multi-field)

## 📝 更新日志

### 最新功能（当前版本）
- ✅ 交互式地图Portal选择工具
- ✅ 从Ingress Intel获取Portal数据
- ✅ Web界面整合所有功能
- ✅ 浏览器脚本快速提取
- ✅ Manim动画可视化

