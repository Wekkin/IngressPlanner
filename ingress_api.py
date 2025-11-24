#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ingress Intel API工具
从Ingress Intel地图获取Portal数据
"""

import json
import requests
import time
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs
import re
from planner import Portal, IngressPlanner


class IngressIntelAPI:
    """Ingress Intel API接口"""
    
    BASE_URL = "https://intel.ingress.com/intel"
    
    def __init__(self, cookies_file: Optional[str] = None):
        """
        初始化API
        
        Args:
            cookies_file: Cookie文件路径（用于认证）
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if cookies_file:
            self.load_cookies(cookies_file)
    
    def load_cookies(self, cookies_file: str):
        """从文件加载Cookies"""
        try:
            with open(cookies_file, 'r') as f:
                cookies = json.load(f)
                self.session.cookies.update(cookies)
            print("✓ Cookies已加载")
        except Exception as e:
            print(f"警告：加载Cookies失败: {e}")
    
    def get_portals_in_tile(self, tile_key: str) -> List[Dict]:
        """
        获取指定tile中的Portal
        
        Args:
            tile_key: Intel地图的tile key
            
        Returns:
            Portal列表
        """
        url = f"{self.BASE_URL}/tile/getEntities"
        params = {
            'tileKeys': tile_key
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('result', [])
        except Exception as e:
            print(f"获取tile数据失败: {e}")
            return []
    
    def get_portals_in_area(self, north: float, south: float, 
                           east: float, west: float, 
                           zoom: int = 15) -> List[Dict]:
        """
        获取指定区域内的所有Portal
        
        Args:
            north: 北边界纬度
            south: 南边界纬度
            east: 东边界经度
            west: 西边界经度
            zoom: 缩放级别
            
        Returns:
            Portal列表
        """
        from math import floor, log, tan, pi, cos
        
        def deg2num(lat_deg, lon_deg, zoom):
            """将经纬度转换为tile坐标"""
            lat_rad = lat_deg * pi / 180.0
            n = 2.0 ** zoom
            xtile = int((lon_deg + 180.0) / 360.0 * n)
            ytile = int((1.0 - log(tan(lat_rad) + (1 / cos(lat_rad))) / pi) / 2.0 * n)
            return (xtile, ytile)
        
        def num2key(x, y, z):
            """将tile坐标转换为key"""
            key = ""
            for i in range(z, 0, -1):
                digit = 0
                mask = 1 << (i - 1)
                if (x & mask) != 0:
                    digit += 1
                if (y & mask) != 0:
                    digit += 2
                key += str(digit)
            return key
        
        # 计算需要的tile范围
        min_tile = deg2num(south, west, zoom)
        max_tile = deg2num(north, east, zoom)
        
        portals = []
        tile_keys = []
        
        # 生成所有tile keys
        for x in range(min_tile[0], max_tile[0] + 1):
            for y in range(min_tile[1], max_tile[1] + 1):
                tile_key = num2key(x, y, zoom)
                tile_keys.append(tile_key)
        
        # 分批获取（避免请求过多）
        batch_size = 50
        for i in range(0, len(tile_keys), batch_size):
            batch = tile_keys[i:i+batch_size]
            url = f"{self.BASE_URL}/tile/getEntities"
            params = {'tileKeys': ','.join(batch)}
            
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'result' in data:
                    for tile_data in data['result']:
                        if 'gameEntities' in tile_data:
                            for entity in tile_data['gameEntities']:
                                if entity[2] == 'p':  # 'p'表示Portal
                                    portals.append(entity)
                
                time.sleep(0.5)  # 避免请求过快
                
            except Exception as e:
                print(f"获取tile数据失败: {e}")
                continue
        
        return portals
    
    def parse_portal_entity(self, entity: List) -> Optional[Dict]:
        """
        解析Portal实体数据
        
        Args:
            entity: Portal实体数据列表
            
        Returns:
            解析后的Portal字典
        """
        try:
            # Intel API返回格式: [guid, timestamp, type, data]
            if len(entity) < 4:
                return None
            
            data = entity[3]  # Portal详细数据
            if isinstance(data, str):
                data = json.loads(data)
            
            portal_info = {
                'guid': entity[0],
                'lat': data.get('latE6', 0) / 1e6,
                'lon': data.get('lngE6', 0) / 1e6,
                'name': data.get('title', 'Unknown'),
                'image': data.get('image'),
            }
            
            return portal_info
            
        except Exception as e:
            print(f"解析Portal数据失败: {e}")
            return None
    
    def extract_portals_from_url(self, intel_url: str) -> List[Dict]:
        """
        从Intel URL提取Portal信息
        
        Args:
            intel_url: Ingress Intel地图URL
            
        Returns:
            Portal列表
        """
        try:
            # 解析URL参数
            parsed = urlparse(intel_url)
            params = parse_qs(parsed.query)
            
            # 提取地图参数
            ll = params.get('ll', [None])[0]
            z = params.get('z', [None])[0]
            
            if ll:
                lat, lon = map(float, ll.split(','))
                zoom = int(z) if z else 15
                
                # 计算区域范围（根据zoom级别）
                delta = 0.01 * (2 ** (15 - zoom))
                
                portals = self.get_portals_in_area(
                    lat + delta, lat - delta,
                    lon + delta, lon - delta,
                    zoom
                )
                
                parsed_portals = []
                for entity in portals:
                    portal = self.parse_portal_entity(entity)
                    if portal:
                        parsed_portals.append(portal)
                
                return parsed_portals
            
        except Exception as e:
            print(f"从URL提取Portal失败: {e}")
        
        return []


def export_portals_to_file(portals: List[Dict], filename: str, format: str = 'txt'):
    """导出Portal到文件"""
    if format == 'txt':
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# 从Ingress Intel获取的Portal坐标\n")
            f.write("# 格式：name,lat,lon\n\n")
            for portal in portals:
                name = portal.get('name', 'Unknown')
                lat = portal.get('lat', 0)
                lon = portal.get('lon', 0)
                f.write(f"{name},{lat},{lon}\n")
    elif format == 'json':
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(portals, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 已导出 {len(portals)} 个Portal到 {filename}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='从Ingress Intel获取Portal数据')
    parser.add_argument('--url', type=str,
                       help='Ingress Intel地图URL')
    parser.add_argument('--area', nargs=4, type=float, metavar=('NORTH', 'SOUTH', 'EAST', 'WEST'),
                       help='区域范围（北、南、东、西边界）')
    parser.add_argument('--cookies', type=str,
                       help='Cookies文件路径（用于认证）')
    parser.add_argument('--output', '-o', type=str, default='portals_from_intel.txt',
                       help='输出文件')
    parser.add_argument('--format', choices=['txt', 'json'], default='txt',
                       help='输出格式')
    
    args = parser.parse_args()
    
    # 创建API实例
    api = IngressIntelAPI(cookies_file=args.cookies)
    
    portals = []
    
    if args.url:
        # 从URL获取
        print(f"正在从URL获取Portal: {args.url}")
        portals = api.extract_portals_from_url(args.url)
    
    elif args.area:
        # 从区域获取
        north, south, east, west = args.area
        print(f"正在获取区域内的Portal: N={north}, S={south}, E={east}, W={west}")
        entities = api.get_portals_in_area(north, south, east, west)
        for entity in entities:
            portal = api.parse_portal_entity(entity)
            if portal:
                portals.append(portal)
    
    else:
        print("错误：需要提供--url或--area参数")
        return
    
    if portals:
        export_portals_to_file(portals, args.output, args.format)
        print(f"\n找到 {len(portals)} 个Portal:")
        for portal in portals[:10]:  # 显示前10个
            print(f"  - {portal['name']}: ({portal['lat']:.6f}, {portal['lon']:.6f})")
        if len(portals) > 10:
            print(f"  ... 还有 {len(portals) - 10} 个Portal")
    else:
        print("未找到Portal，可能需要登录认证")


if __name__ == '__main__':
    main()

