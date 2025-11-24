#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
交互式地图Portal选择工具
使用Folium创建地图，支持点击选择Portal坐标
"""

import folium
from folium import plugins
import json
import os
import webbrowser
from typing import List, Tuple, Optional
from planner import IngressPlanner, Portal


class MapPortalSelector:
    """交互式地图Portal选择器"""
    
    def __init__(self, center_lat: float = 40.008, center_lon: float = 116.327, 
                 zoom_start: int = 15):
        """
        初始化地图选择器
        
        Args:
            center_lat: 地图中心纬度
            center_lon: 地图中心经度
            zoom_start: 初始缩放级别
        """
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.zoom_start = zoom_start
        self.portals = []  # [(name, lat, lon), ...]
        self.map = None
        
    def create_map(self):
        """创建交互式地图"""
        # 使用OpenStreetMap作为底图
        self.map = folium.Map(
            location=[self.center_lat, self.center_lon],
            zoom_start=self.zoom_start,
            tiles='OpenStreetMap'
        )
        
        # 添加多种地图图层选项
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google Satellite',
            name='Google卫星图',
            overlay=False,
            control=True
        ).add_to(self.map)
        
        folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr='Google Map',
            name='Google地图',
            overlay=False,
            control=True
        ).add_to(self.map)
        
        # 添加全屏按钮
        plugins.Fullscreen().add_to(self.map)
        
        # 添加测量工具
        plugins.MeasureControl().add_to(self.map)
        
        # 添加绘制工具
        draw = plugins.Draw(
            export=True,
            position='topleft',
            draw_options={
                'polyline': False,
                'rectangle': False,
                'polygon': False,
                'circle': False,
                'marker': True,
                'circlemarker': False
            },
            edit_options={'edit': True, 'remove': True}
        )
        draw.add_to(self.map)
        
        # 添加JavaScript来处理点击事件
        self._add_click_handler()
        
        # 加载已存在的Portal（如果有）
        if self.portals:
            self._add_existing_portals()
    
    def _add_click_handler(self):
        """添加地图点击处理JavaScript"""
        click_js = """
        <script>
        var portals = [];
        
        function onMapClick(e) {
            var lat = e.latlng.lat;
            var lon = e.latlng.lng;
            var name = prompt('请输入Portal名称（可选）:');
            if (name === null) return;
            
            var portal = {
                name: name || 'Portal' + (portals.length + 1),
                lat: lat,
                lon: lon
            };
            
            portals.push(portal);
            
            // 添加标记
            var marker = L.marker([lat, lon], {
                draggable: true,
                title: portal.name
            }).addTo(map);
            
            marker.bindPopup('<b>' + portal.name + '</b><br>' +
                           '纬度: ' + lat.toFixed(6) + '<br>' +
                           '经度: ' + lon.toFixed(6) + '<br>' +
                           '<button onclick="removePortal(' + (portals.length - 1) + ')">删除</button>');
            
            marker.portalIndex = portals.length - 1;
            
            // 保存到全局变量供Python访问
            window.portals = portals;
            updatePortalList();
        }
        
        function removePortal(index) {
            portals.splice(index, 1);
            map.eachLayer(function(layer) {
                if (layer instanceof L.Marker && layer.portalIndex === index) {
                    map.removeLayer(layer);
                }
            });
            // 重新编号
            map.eachLayer(function(layer) {
                if (layer instanceof L.Marker && layer.portalIndex !== undefined) {
                    if (layer.portalIndex > index) {
                        layer.portalIndex--;
                    }
                }
            });
            window.portals = portals;
            updatePortalList();
        }
        
        function updatePortalList() {
            var list = document.getElementById('portal-list');
            if (!list) return;
            list.innerHTML = '<h3>已选择的Portal (' + portals.length + ')</h3>';
            portals.forEach(function(portal, index) {
                var item = document.createElement('div');
                item.innerHTML = '<strong>' + portal.name + '</strong>: ' +
                               portal.lat.toFixed(6) + ', ' + portal.lon.toFixed(6) +
                               ' <button onclick="removePortal(' + index + ')">删除</button>';
                list.appendChild(item);
            });
        }
        
        function exportPortals() {
            var json = JSON.stringify(portals, null, 2);
            var blob = new Blob([json], {type: 'application/json'});
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'portals.json';
            a.click();
        }
        
        map.on('click', onMapClick);
        </script>
        """
        
        self.map.get_root().html.add_child(folium.Element(click_js))
    
    def _add_existing_portals(self):
        """在地图上添加已存在的Portal"""
        for name, lat, lon in self.portals:
            popup_html = f"""
            <b>{name}</b><br>
            纬度: {lat:.6f}<br>
            经度: {lon:.6f}
            """
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=name,
                icon=folium.Icon(color='blue', icon='info-sign')
            ).add_to(self.map)
    
    def load_portals_from_file(self, filename: str):
        """从文件加载Portal"""
        planner = IngressPlanner()
        planner.load_portals_from_file(filename)
        
        for portal in planner.portals:
            self.portals.append((
                portal.name or f'Portal{portal.id}',
                portal.lat,
                portal.lon
            ))
    
    def add_portal(self, name: str, lat: float, lon: float):
        """添加一个Portal"""
        self.portals.append((name, lat, lon))
        if self.map:
            popup_html = f"""
            <b>{name}</b><br>
            纬度: {lat:.6f}<br>
            经度: {lon:.6f}
            """
            folium.Marker(
                [lat, lon],
                popup=folium.Popup(popup_html, max_width=300),
                tooltip=name
            ).add_to(self.map)
    
    def save_to_file(self, filename: str, format: str = 'txt'):
        """保存Portal到文件"""
        if format == 'txt':
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("# Portal坐标文件\n")
                f.write("# 格式：name,lat,lon\n\n")
                for name, lat, lon in self.portals:
                    f.write(f"{name},{lat},{lon}\n")
        elif format == 'json':
            data = [
                {"name": name, "lat": lat, "lon": lon}
                for name, lat, lon in self.portals
            ]
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✓ 已保存 {len(self.portals)} 个Portal到 {filename}")
    
    def show(self, output_file: str = 'map_portal_selector.html', 
            auto_open: bool = True):
        """显示地图并保存为HTML文件"""
        if not self.map:
            self.create_map()
        
        # 添加侧边栏显示Portal列表
        self._add_sidebar()
        
        # 保存地图
        self.map.save(output_file)
        print(f"✓ 地图已保存到: {output_file}")
        print(f"  请在浏览器中打开该文件，点击地图添加Portal")
        
        if auto_open:
            webbrowser.open(f'file://{os.path.abspath(output_file)}')
    
    def _add_sidebar(self):
        """添加侧边栏显示Portal列表"""
        sidebar_html = """
        <div id="sidebar" style="
            position: fixed;
            top: 10px;
            right: 10px;
            width: 300px;
            background: white;
            padding: 10px;
            border: 2px solid #ccc;
            border-radius: 5px;
            z-index: 1000;
            max-height: 500px;
            overflow-y: auto;
        ">
        <h3>Portal选择器</h3>
        <p>点击地图添加Portal</p>
        <div id="portal-list"></div>
        <button onclick="exportPortals()" style="margin-top: 10px; padding: 5px 10px;">
            导出为JSON
        </button>
        <button onclick="location.reload()" style="margin-top: 5px; padding: 5px 10px;">
            刷新地图
        </button>
        </div>
        """
        
        self.map.get_root().html.add_child(folium.Element(sidebar_html))


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='交互式地图Portal选择工具')
    parser.add_argument('--center-lat', type=float, default=40.008,
                       help='地图中心纬度')
    parser.add_argument('--center-lon', type=float, default=116.327,
                       help='地图中心经度')
    parser.add_argument('--zoom', type=int, default=15,
                       help='初始缩放级别')
    parser.add_argument('--input', '-i', type=str,
                       help='从文件加载已有Portal')
    parser.add_argument('--output', '-o', type=str, default='map_portal_selector.html',
                       help='输出HTML文件')
    
    args = parser.parse_args()
    
    # 创建选择器
    selector = MapPortalSelector(
        center_lat=args.center_lat,
        center_lon=args.center_lon,
        zoom_start=args.zoom
    )
    
    # 加载已有Portal
    if args.input and os.path.exists(args.input):
        selector.load_portals_from_file(args.input)
        print(f"✓ 从 {args.input} 加载了 {len(selector.portals)} 个Portal")
    
    # 显示地图
    selector.show(output_file=args.output)


if __name__ == '__main__':
    main()

