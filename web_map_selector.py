#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Web版交互式地图Portal选择器
提供Flask Web界面，整合地图选择和Portal管理
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import json
import os
from typing import List, Dict
from planner import IngressPlanner

app = Flask(__name__)

# 全局Portal存储（实际使用中应该使用数据库）
portals_storage = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ingress Portal选择器</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; font-family: Arial, sans-serif; }
        #map { height: 100vh; width: 100%; }
        #sidebar {
            position: fixed;
            top: 10px;
            right: 10px;
            width: 350px;
            background: white;
            padding: 15px;
            border: 2px solid #007bff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            max-height: 90vh;
            overflow-y: auto;
        }
        .portal-item {
            padding: 8px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .portal-item:hover {
            background: #e9ecef;
        }
        button {
            padding: 5px 10px;
            margin: 2px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            background: #007bff;
            color: white;
        }
        button:hover {
            background: #0056b3;
        }
        button.danger {
            background: #dc3545;
        }
        button.danger:hover {
            background: #c82333;
        }
        input[type="text"] {
            padding: 5px;
            margin: 5px 0;
            width: 100%;
            box-sizing: border-box;
        }
        h3 {
            margin-top: 0;
            color: #007bff;
        }
    </style>
</head>
<body>
    <div id="map"></div>
    <div id="sidebar">
        <h3>📍 Portal选择器</h3>
        
        <div>
            <input type="text" id="portal-name" placeholder="Portal名称（可选）">
            <button onclick="enableClickMode()">🖱️ 点击地图添加</button>
        </div>
        
        <div style="margin-top: 10px;">
            <button onclick="loadFromFile()">📁 从文件加载</button>
            <button onclick="exportToFile()">💾 导出为文件</button>
            <button onclick="clearAll()" class="danger">🗑️ 清空</button>
        </div>
        
        <div style="margin-top: 10px;">
            <h4>从Ingress获取</h4>
            <input type="text" id="intel-url" placeholder="粘贴Ingress Intel URL">
            <button onclick="fetchFromIntel()">🔍 获取Portal</button>
        </div>
        
        <hr>
        <h4>已选择的Portal (<span id="portal-count">0</span>)</h4>
        <div id="portal-list"></div>
    </div>

    <script>
        var map = L.map('map').setView([40.008, 116.327], 15);
        var portals = [];
        var clickMode = false;
        var markers = [];
        
        // 添加地图图层
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        // Google卫星图
        var googleSat = L.tileLayer('https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', {
            attribution: '© Google',
            maxZoom: 20
        });
        
        // 图层控制
        var baseMaps = {
            "OpenStreetMap": L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '© OpenStreetMap contributors'
            }),
            "Google卫星图": googleSat
        };
        L.control.layers(baseMaps).addTo(map);
        
        // 地图点击事件
        map.on('click', function(e) {
            if (clickMode) {
                var name = document.getElementById('portal-name').value || 
                          'Portal' + (portals.length + 1);
                addPortal(name, e.latlng.lat, e.latlng.lng);
                document.getElementById('portal-name').value = '';
                clickMode = false;
            }
        });
        
        function enableClickMode() {
            clickMode = true;
            alert('点击地图添加Portal');
        }
        
        function addPortal(name, lat, lon) {
            var portal = {name: name, lat: lat, lon: lon};
            portals.push(portal);
            
            var marker = L.marker([lat, lon], {draggable: true})
                .bindPopup('<b>' + name + '</b><br>' +
                          '纬度: ' + lat.toFixed(6) + '<br>' +
                          '经度: ' + lon.toFixed(6) + '<br>' +
                          '<button onclick="removePortal(' + (portals.length - 1) + ')">删除</button>')
                .addTo(map);
            
            marker.on('dragend', function() {
                var newLat = marker.getLatLng().lat;
                var newLon = marker.getLatLng().lng;
                portal.lat = newLat;
                portal.lon = newLon;
                updatePortalList();
            });
            
            markers.push(marker);
            updatePortalList();
        }
        
        function removePortal(index) {
            portals.splice(index, 1);
            if (markers[index]) {
                map.removeLayer(markers[index]);
                markers.splice(index, 1);
            }
            updatePortalList();
        }
        
        function updatePortalList() {
            var list = document.getElementById('portal-list');
            var count = document.getElementById('portal-count');
            count.textContent = portals.length;
            
            list.innerHTML = '';
            portals.forEach(function(portal, index) {
                var item = document.createElement('div');
                item.className = 'portal-item';
                item.innerHTML = 
                    '<div>' +
                        '<strong>' + portal.name + '</strong><br>' +
                        '<small>' + portal.lat.toFixed(6) + ', ' + portal.lon.toFixed(6) + '</small>' +
                    '</div>' +
                    '<button onclick="removePortal(' + index + ')" class="danger">删除</button>';
                list.appendChild(item);
            });
        }
        
        function exportToFile() {
            if (portals.length === 0) {
                alert('没有Portal可导出');
                return;
            }
            
            var content = '# Portal坐标文件\n# 格式：name,lat,lon\n\n';
            portals.forEach(function(portal) {
                content += portal.name + ',' + portal.lat + ',' + portal.lon + '\n';
            });
            
            // 通过API保存
            fetch('/export', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({portals: portals})
            })
            .then(response => response.blob())
            .then(blob => {
                var url = window.URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = url;
                a.download = 'portals.txt';
                a.click();
            });
        }
        
        function loadFromFile() {
            var input = document.createElement('input');
            input.type = 'file';
            input.accept = '.txt,.json';
            input.onchange = function(e) {
                var file = e.target.files[0];
                var reader = new FileReader();
                reader.onload = function(e) {
                    var content = e.target.result;
                    var lines = content.split('\n');
                    
                    lines.forEach(function(line) {
                        line = line.trim();
                        if (line && !line.startsWith('#')) {
                            var parts = line.split(',');
                            if (parts.length >= 2) {
                                var name = parts.length >= 3 ? parts[0] : 'Portal' + (portals.length + 1);
                                var lat = parseFloat(parts[parts.length - 2]);
                                var lon = parseFloat(parts[parts.length - 1]);
                                if (!isNaN(lat) && !isNaN(lon)) {
                                    addPortal(name, lat, lon);
                                }
                            }
                        }
                    });
                };
                reader.readAsText(file);
            };
            input.click();
        }
        
        function clearAll() {
            if (confirm('确定要清空所有Portal吗？')) {
                portals = [];
                markers.forEach(function(marker) {
                    map.removeLayer(marker);
                });
                markers = [];
                updatePortalList();
            }
        }
        
        function fetchFromIntel() {
            var url = document.getElementById('intel-url').value;
            if (!url) {
                alert('请输入Ingress Intel URL');
                return;
            }
            
            fetch('/fetch_intel', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: url})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    data.portals.forEach(function(portal) {
                        addPortal(portal.name, portal.lat, portal.lon);
                    });
                    alert('成功获取 ' + data.count + ' 个Portal');
                } else {
                    alert('获取失败: ' + data.error);
                }
            })
            .catch(error => {
                alert('错误: ' + error);
            });
        }
        
        // 从URL参数加载Portal
        var urlParams = new URLSearchParams(window.location.search);
        var portalsParam = urlParams.get('portals');
        if (portalsParam) {
            try {
                var loadedPortals = JSON.parse(decodeURIComponent(portalsParam));
                loadedPortals.forEach(function(portal) {
                    addPortal(portal.name, portal.lat, portal.lon);
                });
            } catch(e) {
                console.error('Failed to load portals from URL', e);
            }
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """主页面"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/export', methods=['POST'])
def export_portals():
    """导出Portal到文件"""
    data = request.json
    portals = data.get('portals', [])
    
    if not portals:
        return jsonify({'error': '没有Portal可导出'}), 400
    
    # 生成文件内容
    content = "# Portal坐标文件\n# 格式：name,lat,lon\n\n"
    for portal in portals:
        name = portal.get('name', 'Unknown')
        lat = portal.get('lat', 0)
        lon = portal.get('lon', 0)
        content += f"{name},{lat},{lon}\n"
    
    # 创建临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_file = f.name
    
    return send_file(temp_file, as_attachment=True, download_name='portals.txt')


@app.route('/fetch_intel', methods=['POST'])
def fetch_from_intel():
    """从Ingress Intel获取Portal"""
    data = request.json
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'URL不能为空'}), 400
    
    try:
        from ingress_api import IngressIntelAPI
        api = IngressIntelAPI()
        portals = api.extract_portals_from_url(url)
        
        portal_list = []
        for portal in portals:
            portal_list.append({
                'name': portal.get('name', 'Unknown'),
                'lat': portal.get('lat', 0),
                'lon': portal.get('lon', 0)
            })
        
        return jsonify({
            'success': True,
            'count': len(portal_list),
            'portals': portal_list
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("Ingress Portal选择器 - Web版本")
    print("=" * 60)
    print("正在启动服务器...")
    print("请在浏览器中访问: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)

