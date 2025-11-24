#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ingress多重控制场规划器
根据地图上的Portal点，计算最优化的连接方式和最短路径
"""

import math
import argparse
from typing import List, Tuple, Dict, Set, Optional
from dataclasses import dataclass
from collections import defaultdict
import numpy as np
from scipy.spatial import Delaunay
from geopy.distance import geodesic


# Ingress AP规则
LINK_AP = {
    1: 313,    # 1-5km
    2: 1250,   # 5-10km
    3: 1563,   # 10-25km
    4: 2500,   # 25-50km
    5: 3125,   # 50-100km
    6: 3750,   # 100-150km
    7: 4375,   # 150-200km
    8: 5000,   # 200km+
}
FIELD_AP = 1250  # 每个field的AP值


@dataclass
class Portal:
    """Portal点"""
    id: int
    name: Optional[str]
    lat: float
    lon: float

    def __hash__(self):
        return hash((self.id, self.lat, self.lon))

    def __eq__(self, other):
        return self.id == other.id


@dataclass
class Link:
    """连接两个Portal的link"""
    portal1: Portal
    portal2: Portal
    distance: float  # 单位：米
    
    @property
    def ap(self) -> int:
        """根据距离计算link的AP值"""
        km = self.distance / 1000.0
        if km < 1:
            return 0
        elif km < 5:
            return LINK_AP[1]
        elif km < 10:
            return LINK_AP[2]
        elif km < 25:
            return LINK_AP[3]
        elif km < 50:
            return LINK_AP[4]
        elif km < 100:
            return LINK_AP[5]
        elif km < 150:
            return LINK_AP[6]
        elif km < 200:
            return LINK_AP[7]
        else:
            return LINK_AP[8]
    
    def __hash__(self):
        return hash((min(self.portal1.id, self.portal2.id), 
                    max(self.portal1.id, self.portal2.id)))
    
    def __eq__(self, other):
        if not isinstance(other, Link):
            return False
        ids1 = (min(self.portal1.id, self.portal2.id), 
                max(self.portal1.id, self.portal2.id))
        ids2 = (min(other.portal1.id, other.portal2.id), 
                max(other.portal1.id, other.portal2.id))
        return ids1 == ids2


@dataclass
class Field:
    """由三个Portal形成的field"""
    portal1: Portal
    portal2: Portal
    portal3: Portal
    links: Tuple[Link, Link, Link]
    
    @property
    def ap(self) -> int:
        """field的AP值"""
        return FIELD_AP
    
    def contains_portal(self, portal: Portal) -> bool:
        """判断field是否包含某个portal"""
        return portal in [self.portal1, self.portal2, self.portal3]


@dataclass
class Solution:
    """连接方案"""
    links: List[Link]
    fields: List[Field]
    total_ap: int
    distance: float  # 行走距离（米）
    path: List[Portal]  # 连接路径
    
    def __str__(self):
        result = []
        result.append(f"总AP: {self.total_ap}")
        result.append(f"Link数量: {len(self.links)}")
        result.append(f"Field数量: {len(self.fields)}")
        result.append(f"行走距离: {self.distance/1000:.2f} km")
        result.append("\n连接方案:")
        for i, link in enumerate(self.links):
            result.append(f"{i}: ({link.portal1.lat}, {link.portal1.lon})->"
                         f"({link.portal2.lat}, {link.portal2.lon})")
        return "\n".join(result)


@dataclass
class AgentPlan:
    """单个agent的连接方案"""
    links: List[Link]
    fields: List[Field]
    ap: int
    distance: float
    path: List[Portal]


@dataclass
class MultiAgentSolution:
    """多人规划方案"""
    agent_plans: List[AgentPlan]
    total_ap: int
    
    def __str__(self):
        result = [f"总AP: {self.total_ap}", f"Agent数量: {len(self.agent_plans)}"]
        for i, plan in enumerate(self.agent_plans):
            result.append(f"\nAgent {i}:")
            result.append(f"  AP: {plan.ap}")
            result.append(f"  行走距离: {plan.distance/1000:.2f} km")
            result.append(f"  Link数量: {len(plan.links)}")
        return "\n".join(result)


class IngressPlanner:
    """Ingress多重控制场规划器"""
    
    def __init__(self):
        self.portals: List[Portal] = []
        self.possible_links: List[Link] = []
        self.possible_fields: List[Field] = []
    
    def add_portal(self, lat: float, lon: float, name: Optional[str] = None) -> Portal:
        """添加一个Portal点"""
        portal = Portal(id=len(self.portals), name=name, lat=lat, lon=lon)
        self.portals.append(portal)
        return portal
    
    def load_portals_from_file(self, filename: str):
        """从文件加载Portal坐标"""
        self.portals = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(',')
                if len(parts) >= 2:
                    try:
                        if len(parts) == 2:
                            lat, lon = float(parts[0]), float(parts[1])
                            name = None
                        else:
                            name, lat, lon = parts[0], float(parts[1]), float(parts[2])
                        self.add_portal(lat, lon, name)
                    except ValueError:
                        continue
    
    def _calculate_distance(self, p1: Portal, p2: Portal) -> float:
        """计算两个Portal之间的距离（米）"""
        return geodesic((p1.lat, p1.lon), (p2.lat, p2.lon)).meters
    
    def _generate_possible_links(self) -> List[Link]:
        """生成所有可能的link（基于Delaunay三角剖分）"""
        if len(self.portals) < 2:
            return []
        
        # 使用Delaunay三角剖分找到可行的连接
        points = np.array([[p.lat, p.lon] for p in self.portals])
        tri = Delaunay(points)
        
        links = []
        link_set = set()
        
        # 从三角剖分中提取边
        for simplex in tri.simplices:
            for i in range(3):
                p1_id, p2_id = simplex[i], simplex[(i+1) % 3]
                if p1_id > p2_id:
                    p1_id, p2_id = p2_id, p1_id
                
                if (p1_id, p2_id) not in link_set:
                    link_set.add((p1_id, p2_id))
                    p1, p2 = self.portals[p1_id], self.portals[p2_id]
                    distance = self._calculate_distance(p1, p2)
                    links.append(Link(p1, p2, distance))
        
        return links
    
    def _check_link_intersection(self, link1: Link, link2: Link) -> bool:
        """检查两个link是否相交（除了在portal处）"""
        # 如果link共享portal，不算相交
        if (link1.portal1 == link2.portal1 or link1.portal1 == link2.portal2 or
            link1.portal2 == link2.portal1 or link1.portal2 == link2.portal2):
            return False
        
        # 使用shapely检查线段是否相交
        try:
            from shapely.geometry import LineString, Point
            
            line1 = LineString([(link1.portal1.lon, link1.portal1.lat),
                               (link1.portal2.lon, link1.portal2.lat)])
            line2 = LineString([(link2.portal1.lon, link2.portal1.lat),
                               (link2.portal2.lon, link2.portal2.lat)])
            
            return line1.intersects(line2) and not line1.touches(line2)
        except ImportError:
            # 如果没有shapely，使用简单的数学方法
            return self._line_segments_intersect(
                (link1.portal1.lon, link1.portal1.lat),
                (link1.portal2.lon, link1.portal2.lat),
                (link2.portal1.lon, link2.portal1.lat),
                (link2.portal2.lon, link2.portal2.lat)
            )
    
    def _line_segments_intersect(self, p1, p2, p3, p4):
        """检查两条线段是否相交（数学方法）"""
        def ccw(A, B, C):
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)
    
    def _generate_fields(self, links: List[Link]) -> List[Field]:
        """从links生成所有可能的fields"""
        fields = []
        field_set = set()  # 用于去重
        
        # 构建portal到links的映射
        portal_links = defaultdict(list)
        for link in links:
            portal_links[link.portal1].append(link)
            portal_links[link.portal2].append(link)
        
        # 对于每个link，查找可以形成field的第三个portal
        for link in links:
            p1, p2 = link.portal1, link.portal2
            
            # 找到同时连接到p1和p2的portal
            p1_neighbors = {l.portal2 if l.portal1 == p1 else l.portal1 
                          for l in portal_links[p1]}
            p2_neighbors = {l.portal2 if l.portal1 == p2 else l.portal1 
                          for l in portal_links[p2]}
            
            common_neighbors = p1_neighbors & p2_neighbors
            
            for p3 in common_neighbors:
                # 使用排序后的portal ID作为唯一标识，避免重复
                portal_ids = tuple(sorted([p1.id, p2.id, p3.id]))
                if portal_ids in field_set:
                    continue
                field_set.add(portal_ids)
                
                # 找到三个link
                link1 = link
                link2 = next(l for l in portal_links[p1] 
                           if (l.portal1 == p3 or l.portal2 == p3))
                link3 = next(l for l in portal_links[p2] 
                           if (l.portal1 == p3 or l.portal2 == p3))
                
                # 创建field
                field = Field(p1, p2, p3, (link1, link2, link3))
                fields.append(field)
        
        return fields
    
    def _check_field_validity(self, field: Field, selected_links: Set[Link]) -> bool:
        """检查field是否有效（所有link都在selected_links中）"""
        return all(link in selected_links for link in field.links)
    
    def _count_points_in_field(self, field: Field, portals: Set[Portal]) -> int:
        """统计field内部包含的portal数量"""
        count = 0
        p1, p2, p3 = field.portal1, field.portal2, field.portal3
        
        # 使用简单的点在三角形内的判断
        for portal in portals:
            if portal in [p1, p2, p3]:
                continue
            if self._point_in_triangle(portal, p1, p2, p3):
                count += 1
        
        return count
    
    def _point_in_triangle(self, p: Portal, p1: Portal, p2: Portal, p3: Portal) -> bool:
        """判断点是否在三角形内（使用重心坐标）"""
        def sign(p1, p2, p3):
            return (p1.lat - p3.lat) * (p2.lon - p3.lon) - (p2.lat - p3.lat) * (p1.lon - p3.lon)
        
        d1 = sign(p, p1, p2)
        d2 = sign(p, p2, p3)
        d3 = sign(p, p3, p1)
        
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        
        return not (has_neg and has_pos)
    
    def _calculate_path_distance(self, path: List[Portal]) -> float:
        """计算路径的总距离"""
        if len(path) < 2:
            return 0.0
        
        total = 0.0
        for i in range(len(path) - 1):
            total += self._calculate_distance(path[i], path[i+1])
        return total
    
    def _greedy_optimize(self, possible_links: List[Link]) -> Solution:
        """使用贪心算法优化连接方案"""
        # 按AP/distance比值排序
        possible_links.sort(key=lambda l: l.ap / max(l.distance, 1), reverse=True)
        
        selected_links = set()
        selected_fields = []
        used_portals = set()
        
        # 贪心选择link
        for link in possible_links:
            # 检查是否与已有link相交
            can_add = True
            for existing_link in selected_links:
                if self._check_link_intersection(link, existing_link):
                    can_add = False
                    break
            
            if can_add:
                selected_links.add(link)
                used_portals.add(link.portal1)
                used_portals.add(link.portal2)
        
        # 生成fields
        all_fields = self._generate_fields(list(selected_links))
        
        # 过滤有效的fields（三角形内最多8个点）
        for field in all_fields:
            points_inside = self._count_points_in_field(field, used_portals)
            if points_inside <= 8:  # 三角形内的点数不超过8
                selected_fields.append(field)
        
        # 计算总AP
        total_link_ap = sum(link.ap for link in selected_links)
        total_field_ap = sum(field.ap for field in selected_fields)
        total_ap = total_link_ap + total_field_ap
        
        # 计算路径（使用最小生成树或贪心路径）
        path = self._generate_path(list(selected_links))
        distance = self._calculate_path_distance(path)
        
        return Solution(
            links=list(selected_links),
            fields=selected_fields,
            total_ap=total_ap,
            distance=distance,
            path=path
        )
    
    def _generate_path(self, links: List[Link]) -> List[Portal]:
        """生成连接这些links的最短路径"""
        if not links:
            return []
        
        # 构建图
        graph = defaultdict(list)
        for link in links:
            graph[link.portal1].append(link.portal2)
            graph[link.portal2].append(link.portal1)
        
        # 找到起点（度数最小的portal）
        start = min(graph.keys(), key=lambda p: len(graph[p]))
        
        # 使用DFS或贪心方法生成路径
        visited_links = set()
        path = [start]
        current = start
        
        while len(visited_links) < len(links):
            best_next = None
            best_distance = float('inf')
            
            for neighbor in graph[current]:
                link = next(l for l in links 
                          if (l.portal1 == current and l.portal2 == neighbor) or
                             (l.portal2 == current and l.portal1 == neighbor))
                
                if link not in visited_links:
                    distance = self._calculate_distance(current, neighbor)
                    if distance < best_distance:
                        best_distance = distance
                        best_next = neighbor
                        best_link = link
            
            if best_next is None:
                # 如果找不到下一个，尝试回到已访问的portal
                for neighbor in graph[current]:
                    link = next(l for l in links 
                              if (l.portal1 == current and l.portal2 == neighbor) or
                                 (l.portal2 == current and l.portal1 == neighbor))
                    if link not in visited_links:
                        best_next = neighbor
                        best_link = link
                        break
                
                if best_next is None:
                    break
            
            visited_links.add(best_link)
            path.append(best_next)
            current = best_next
        
        return path
    
    def plan(self, portals: Optional[List[Tuple[float, float]]] = None) -> Solution:
        """生成最优连接方案"""
        if portals:
            self.portals = []
            for lat, lon in portals:
                self.add_portal(lat, lon)
        
        if len(self.portals) < 3:
            return Solution([], [], 0, 0.0, [])
        
        # 生成所有可能的link
        possible_links = self._generate_possible_links()
        
        if not possible_links:
            return Solution([], [], 0, 0.0, [])
        
        # 优化连接方案
        solution = self._greedy_optimize(possible_links)
        
        return solution
    
    def multi_agent_plan(self, portals: Optional[List[Tuple[float, float]]] = None, 
                        num_agents: int = 3) -> MultiAgentSolution:
        """多人规划"""
        # 先生成完整方案
        solution = self.plan(portals)
        
        if not solution.links:
            return MultiAgentSolution([], 0)
        
        # 按AP平均分配links
        links_per_agent = len(solution.links) // num_agents
        remainder = len(solution.links) % num_agents
        
        agent_plans = []
        start_idx = 0
        
        for i in range(num_agents):
            # 分配links
            num_links = links_per_agent + (1 if i < remainder else 0)
            agent_links = solution.links[start_idx:start_idx + num_links]
            start_idx += num_links
            
            # 计算agent的fields
            agent_link_set = set(agent_links)
            agent_fields = [f for f in solution.fields 
                          if all(l in agent_link_set for l in f.links)]
            
            # 计算AP和距离
            agent_link_ap = sum(l.ap for l in agent_links)
            agent_field_ap = sum(f.ap for f in agent_fields)
            agent_ap = agent_link_ap + agent_field_ap
            
            # 生成路径
            agent_path = self._generate_path(agent_links)
            agent_distance = self._calculate_path_distance(agent_path)
            
            agent_plan = AgentPlan(
                links=agent_links,
                fields=agent_fields,
                ap=agent_ap,
                distance=agent_distance,
                path=agent_path
            )
            agent_plans.append(agent_plan)
        
        return MultiAgentSolution(agent_plans, solution.total_ap)


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description='Ingress多重控制场规划器')
    parser.add_argument('--input', '-i', type=str, help='输入Portal坐标文件')
    parser.add_argument('--output', '-o', type=str, help='输出结果文件')
    parser.add_argument('--agents', '-a', type=int, default=1, help='Agent数量（多人规划）')
    
    args = parser.parse_args()
    
    planner = IngressPlanner()
    
    if args.input:
        planner.load_portals_from_file(args.input)
    else:
        # 使用示例数据
        print("使用示例数据...")
        example_portals = [
            (40.008008, 116.327477),
            (40.008102, 116.326605),
            (40.008034, 116.325578),
        ]
        for lat, lon in example_portals:
            planner.add_portal(lat, lon)
    
    if args.agents > 1:
        solution = planner.multi_agent_plan(num_agents=args.agents)
    else:
        solution = planner.plan()
    
    result_str = str(solution)
    print(result_str)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result_str)
        print(f"\n结果已保存到: {args.output}")


if __name__ == '__main__':
    main()

