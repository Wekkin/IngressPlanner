# Manim可视化指南

本指南介绍如何使用Manim创建Ingress连接方案的动画可视化。

## 安装Manim

### 方式1: 使用pip安装（推荐）

```bash
pip install manim
```

### 方式2: 从源码安装（最新版本）

```bash
git clone https://github.com/ManimCommunity/manim.git
cd manim
pip install -e .
```

### 系统依赖

Manim需要一些系统依赖，根据操作系统安装：

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install build-essential python3-dev libcairo2-dev libpango1.0-dev ffmpeg
```

**macOS:**
```bash
brew install py3cairo ffmpeg
```

**Windows:**
使用conda安装依赖：
```bash
conda install manim -c conda-forge
```

## 基本使用

### 1. 使用示例数据

直接运行场景文件，会自动使用示例数据：

```bash
# 生成低质量预览（快速）
manim -pql ingress_scene.py IngressScene

# 生成高质量视频（慢但清晰）
manim -pqh ingress_scene.py IngressScene
```

### 2. 使用自定义Portal文件

修改 `ingress_scene.py` 文件中的配置：

```python
class IngressScene(Scene):
    CONFIG = {
        "input_file": "portals_zijing.txt",  # 改为你的文件
        "show_labels": True,
    }
```

然后运行：
```bash
manim -pql ingress_scene.py IngressScene
```

### 3. 多人规划动画

```bash
# 修改MultiAgentScene的CONFIG设置num_agents
manim -pql ingress_scene.py MultiAgentScene
```

## 场景类说明

### IngressScene

单人规划方案的可视化场景。

**动画流程：**
1. 显示标题和统计信息
2. 逐个显示Portal点（带标签）
3. 逐步创建Link连接（显示AP值）
4. 填充Field区域（黄色三角形）
5. 动画展示行走路径
6. 标记起点和终点

**配置选项：**
- `input_file`: Portal坐标文件路径
- `show_labels`: 是否显示Portal名称标签

### MultiAgentScene

多人规划方案的可视化场景。

**动画流程：**
1. 显示标题和总AP
2. 显示所有Portal点
3. 为每个Agent依次展示：
   - Agent信息（AP、Links数、距离）
   - Link连接（不同颜色）
   - Field区域（半透明填充）
   - 行走路径（虚线）

**配置选项：**
- `input_file`: Portal坐标文件路径
- `num_agents`: Agent数量

## 渲染质量选项

Manim提供三种渲染质量：

| 参数 | 质量 | 分辨率 | 速度 | 用途 |
|------|------|--------|------|------|
| `-ql` | 低 | 480p | 快 | 快速预览 |
| `-qm` | 中 | 720p | 中 | 一般使用 |
| `-qh` | 高 | 1080p | 慢 | 最终输出 |

**示例：**
```bash
# 快速预览
manim -pql ingress_scene.py IngressScene

# 最终视频
manim -pqh ingress_scene.py IngressScene
```

## 输出文件位置

渲染后的视频保存在：
```
media/videos/ingress_scene/[质量]/IngressScene.mp4
```

例如：
```
media/videos/ingress_scene/720p30/MultiAgentScene.mp4
```

## 自定义动画

### 修改颜色

在场景类的 `construct()` 方法中修改颜色：

```python
# Portal点颜色
outer_circle = Circle(radius=0.15, color=BLUE, ...)  # 改为其他颜色

# Link颜色
line = Line(..., color=GREEN, ...)  # 改为其他颜色

# Field颜色
polygon = Polygon(..., fill_color=YELLOW, ...)  # 改为其他颜色
```

Manim可用颜色：`BLUE`, `RED`, `GREEN`, `YELLOW`, `PURPLE`, `ORANGE`, `PINK`, `TEAL`, `WHITE`, 等

### 修改动画速度

调整 `run_time` 参数：

```python
self.play(Write(title), run_time=1)  # 1秒
self.play(Write(title), run_time=2)  # 2秒（更慢）
```

### 添加更多效果

Manim提供了丰富的动画效果：

```python
# 旋转
self.play(Rotate(obj, PI))

# 缩放
self.play(obj.animate.scale(2))

# 移动
self.play(obj.animate.shift(UP * 2))

# 组合动画
self.play(
    obj1.animate.shift(UP),
    obj2.animate.shift(DOWN),
    run_time=2
)
```

## 常见问题

### Q: 渲染速度很慢怎么办？

A: 使用低质量预览：`manim -pql ingress_scene.py IngressScene`

### Q: 视频不清晰？

A: 使用高质量渲染：`manim -pqh ingress_scene.py IngressScene`

### Q: 如何只渲染不播放？

A: 去掉 `-p` 参数：`manim -ql ingress_scene.py IngressScene`

### Q: Portal位置不正确？

A: 检查坐标归一化函数 `_normalize_coordinates()`，调整缩放比例 `scale`

### Q: 如何导出为GIF？

A: 渲染后使用ffmpeg转换，或使用Manim的GIF支持：
```bash
manim --format=gif -ql ingress_scene.py IngressScene
```

## 进阶技巧

### 1. 添加背景地图

可以导入地图底图作为背景（需要额外处理坐标转换）

### 2. 添加文字说明

使用 `Text` 或 `Tex` 对象添加说明文字

### 3. 添加图表

使用Manim的图表功能显示AP分布、距离统计等

### 4. 交互式场景

Manim支持创建交互式场景（需要特殊配置）

## 参考资料

- [Manim官方文档](https://docs.manim.community/)
- [Manim GitHub](https://github.com/ManimCommunity/manim)
- [Manim示例](https://docs.manim.community/en/stable/examples.html)

