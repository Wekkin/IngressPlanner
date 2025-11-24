# 地图Portal选择工具使用指南

本指南介绍如何使用交互式地图工具和从Ingress获取Portal数据。

## 方式一：交互式地图选择（推荐）

### 1. 使用Folium地图工具（命令行）

创建一个交互式HTML地图，在地图上点击选择Portal：

```bash
# 基本使用（使用默认位置）
python map_selector.py

# 指定地图中心位置
python map_selector.py --center-lat 40.008 --center-lon 116.327 --zoom 15

# 从已有文件加载Portal
python map_selector.py --input portals_zijing.txt --output my_map.html

# 指定输出文件
python map_selector.py --output my_portals_map.html
```

**使用步骤：**
1. 运行命令后会在浏览器中打开地图
2. 点击地图上的任意位置添加Portal
3. 输入Portal名称（可选）
4. 可以拖动标记调整位置
5. 右键删除标记或点击"删除"按钮
6. 点击"导出为JSON"保存数据

### 2. 使用Web界面（Flask）

启动Web服务器，提供完整的Portal管理界面：

```bash
# 启动Web服务器
python web_map_selector.py

# 服务器将在 http://localhost:5000 启动
# 在浏览器中打开该地址
```

**Web界面功能：**
- ✅ 点击地图添加Portal
- ✅ 拖拽标记调整位置
- ✅ 从文件加载Portal
- ✅ 导出Portal数据
- ✅ 从Ingress Intel URL获取Portal
- ✅ 实时显示Portal列表
- ✅ 多种地图图层切换（OpenStreetMap、Google卫星图）

## 方式二：从Ingress Intel获取Portal

### 方法1：使用浏览器扩展脚本（最简单）

**步骤：**
1. 打开 [Ingress Intel地图](https://intel.ingress.com/intel)
2. 登录你的Ingress账号
3. 导航到目标区域
4. 按 `F12` 打开浏览器开发者工具
5. 切换到 "Console"（控制台）标签
6. 复制 `browser_extract.js` 文件中的代码
7. 粘贴到控制台并按回车执行
8. 脚本会自动提取当前可见区域的所有Portal
9. 数据会显示在控制台并自动下载为 `ingress_portals.txt`

**优点：**
- 无需额外配置
- 直接使用浏览器访问Intel地图
- 自动提取可见区域的所有Portal
- 支持登录后的完整数据

### 方法2：使用命令行工具

```bash
# 从Ingress Intel URL获取
python ingress_api.py --url "https://intel.ingress.com/intel?ll=40.008,116.327&z=15"

# 从指定区域获取
python ingress_api.py --area 40.010 40.006 116.330 116.324

# 使用Cookies文件（用于认证）
python ingress_api.py --url "..." --cookies cookies.json

# 指定输出格式
python ingress_api.py --url "..." --output portals.txt --format txt
python ingress_api.py --url "..." --output portals.json --format json
```

**获取Cookies（用于认证）：**
1. 在浏览器中登录 [Ingress Intel](https://intel.ingress.com/intel)
2. 打开开发者工具（F12）
3. 切换到 Network（网络）标签
4. 刷新页面
5. 找到请求 `intel.ingress.com` 的请求
6. 在请求头中找到 `Cookie` 字段
7. 复制Cookie值并保存为JSON格式：

```json
{
  "SESSIONID": "your-session-id",
  "csrftoken": "your-csrf-token"
}
```

保存为 `cookies.json` 文件使用。

### 方法3：在Web界面中使用

1. 启动Web服务器：`python web_map_selector.py`
2. 在浏览器中打开 `http://localhost:5000`
3. 在侧边栏找到"从Ingress获取"部分
4. 粘贴Ingress Intel URL
5. 点击"获取Portal"按钮
6. Portal会自动添加到地图上

## 工具对比

| 功能 | Folium地图 | Web界面 | 浏览器脚本 | API工具 |
|------|-----------|---------|-----------|---------|
| 点击选择Portal | ✅ | ✅ | ❌ | ❌ |
| 拖拽调整位置 | ✅ | ✅ | ❌ | ❌ |
| 从Intel获取 | ❌ | ✅ | ✅ | ✅ |
| 文件管理 | ✅ | ✅ | ❌ | ✅ |
| 实时预览 | ✅ | ✅ | ❌ | ❌ |
| 多地图图层 | ✅ | ✅ | ❌ | ❌ |
| 需要登录 | ❌ | ❌ | ✅ | ✅ |

## 推荐工作流程

### 场景1：手动选择Portal

1. 启动Web界面：`python web_map_selector.py`
2. 在浏览器中打开并导航到目标区域
3. 逐个点击地图添加Portal
4. 可以切换到卫星图查看实际位置
5. 导出为文件：`portals.txt`

### 场景2：从Ingress获取大量Portal

1. 在Intel地图上导航到目标区域
2. 使用浏览器脚本（`browser_extract.js`）提取Portal
3. 保存导出的 `ingress_portals.txt` 文件
4. 在Web界面中加载该文件进行编辑和优化

### 场景3：混合使用

1. 从Ingress获取基础Portal列表
2. 在Web界面中加载并查看
3. 添加或删除Portal
4. 调整Portal位置
5. 导出最终结果

## 常见问题

### Q: 地图加载慢怎么办？

A: 
- 使用离线地图（需要配置）
- 或者使用Google地图图层
- 减少地图缩放级别

### Q: 从Ingress获取不到Portal？

A: 
- 确保已登录Ingress账号
- 使用浏览器脚本方式（最简单）
- 或者配置Cookies文件
- 检查网络连接

### Q: 如何批量导入Portal？

A: 
- 使用文件导入功能
- 支持TXT格式（name,lat,lon）
- 支持JSON格式

### Q: 导出的文件格式是什么？

A: 
- TXT格式：`Portal名称,纬度,经度`
- JSON格式：包含完整Portal信息的JSON对象

### Q: 可以在移动设备上使用吗？

A: 
- Web界面支持移动设备访问
- 在局域网中启动服务器，使用设备IP访问
- 例如：`http://192.168.1.100:5000`

## 文件格式说明

### TXT格式

```
# Portal坐标文件
# 格式：name,lat,lon

Portal1,40.008008,116.327477
Portal2,40.008102,116.326605
```

### JSON格式

```json
[
  {
    "name": "Portal1",
    "lat": 40.008008,
    "lon": 116.327477
  },
  {
    "name": "Portal2",
    "lat": 40.008102,
    "lon": 116.326605
  }
]
```

## 下一步

获取Portal数据后，可以使用规划器生成连接方案：

```bash
python planner.py --input portals.txt --output solution.txt
```

然后使用可视化工具查看结果：

```bash
python visualize.py --input portals.txt --output result.png
manim -pql ingress_scene.py IngressScene
```

