#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
使用Manim创建Ingress连接方案的可视化动画
"""

from manim import *
import numpy as np
from planner import IngressPlanner, Solution, Portal, Link, Field
from typing import List, Optional
import argparse


class IngressVisualization(Scene):
    """Ingress连接方案动画可视化场景"""
    
    def __init__(self, solution: Solution, planner: IngressPlanner, 
                 show_labels: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.solution = solution
        self.planner = planner
        self.show_labels = show_labels
        
        # 坐标转换：将经纬度转换为屏幕坐标
        self.portal_positions = {}
        self._normalize_coordinates()
    
    def _normalize_coordinates(self):
        """将经纬度坐标归一化到屏幕坐标系"""
        if not self.solution.links:
            return
        
        # 收集所有portal
        all_portals = set()
        for link in self.solution.links:
            all_portals.add(link.portal1)
            all_portals.add(link.portal2)
        
        # 获取经纬度范围
        lats = [p.lat for p in all_portals]
        lons = [p.lon for p in all_portals]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        # 计算中心点和范围
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        range_lat = max_lat - min_lat if max_lat != min_lat else 0.01
        range_lon = max_lon - min_lon if max_lon != min_lon else 0.01
        
        # 归一化到屏幕坐标（保留比例）
        scale = 5.0 / max(range_lat, range_lon * 0.7)  # 0.7是纬度到经度的近似比例
        
        for portal in all_portals:
            x = (portal.lon - center_lon) * scale * 0.7
            y = (portal.lat - center_lat) * scale
            self.portal_positions[portal] = np.array([x, y, 0])
    
    def get_portal_position(self, portal: Portal):
        """获取portal在屏幕上的位置"""
        return self.portal_positions.get(portal, ORIGIN)
    
    def construct(self):
        """构建动画场景"""
        if not self.solution.links:
            text = Text("没有连接方案可展示", font_size=48)
            self.play(Write(text))
            self.wait(2)
            return
        
        # 1. 标题
        title = Text("Ingress 多重控制场规划方案", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # 2. 显示统计信息
        stats_text = (
            f"总AP: {self.solution.total_ap}  |  "
            f"Links: {len(self.solution.links)}  |  "
            f"Fields: {len(self.solution.fields)}  |  "
            f"距离: {self.solution.distance/1000:.2f}km"
        )
        stats = Text(stats_text, font_size=24)
        stats.next_to(title, DOWN, buff=0.3)
        self.play(Write(stats))
        self.wait(0.5)
        
        # 3. 显示所有Portal点
        portal_dots = {}
        portal_labels = {}
        all_portals = set()
        
        for link in self.solution.links:
            all_portals.add(link.portal1)
            all_portals.add(link.portal2)
        
        portal_animations = []
        for portal in all_portals:
            pos = self.get_portal_position(portal)
            dot = Dot(point=pos, radius=0.08, color=BLUE)
            portal_dots[portal] = dot
            
            if self.show_labels and portal.name:
                label = Text(portal.name, font_size=16)
                label.next_to(dot, UR, buff=0.1)
                portal_labels[portal] = label
                portal_animations.append(FadeIn(dot, label))
            else:
                portal_animations.append(FadeIn(dot))
        
        self.play(*portal_animations, lag_ratio=0.1)
        self.wait(0.5)
        
        # 4. 逐步显示Links
        link_lines = {}
        link_animations = []
        
        for i, link in enumerate(self.solution.links):
            p1_pos = self.get_portal_position(link.portal1)
            p2_pos = self.get_portal_position(link.portal2)
            line = Line(p1_pos, p2_pos, color=GREEN, stroke_width=3)
            link_lines[link] = line
            
            # 添加AP标签（可选）
            mid_point = (p1_pos + p2_pos) / 2
            ap_label = Text(str(link.ap), font_size=12, color=GREEN)
            ap_label.move_to(mid_point)
            
            link_animations.append(
                AnimationGroup(
                    Create(line),
                    FadeIn(ap_label, scale=0.5),
                    lag_ratio=0.3
                )
            )
        
        self.play(*link_animations, lag_ratio=0.2)
        self.wait(0.5)
        
        # 5. 显示Fields（三角形填充）
        field_polygons = {}
        field_animations = []
        
        for field in self.solution.fields:
            p1_pos = self.get_portal_position(field.portal1)
            p2_pos = self.get_portal_position(field.portal2)
            p3_pos = self.get_portal_position(field.portal3)
            
            polygon = Polygon(p1_pos, p2_pos, p3_pos, 
                            fill_opacity=0.3, fill_color=YELLOW,
                            stroke_width=0)
            field_polygons[field] = polygon
            field_animations.append(FadeIn(polygon, scale=0.8))
        
        if field_animations:
            self.play(*field_animations, lag_ratio=0.1)
            self.wait(0.5)
        
        # 6. 显示路径（如果存在）
        if self.solution.path and len(self.solution.path) > 1:
            path_points = [self.get_portal_position(p) for p in self.solution.path]
            path_line = VMobject()
            path_line.set_points_as_corners(path_points)
            path_line.set_stroke(color=RED, width=2, opacity=0.8)
            path_line.set_stroke_dasharray([5, 5])
            
            # 路径动画
            self.play(Create(path_line), run_time=2)
            
            # 标记起点和终点
            start_pos = self.get_portal_position(self.solution.path[0])
            end_pos = self.get_portal_position(self.solution.path[-1])
            
            start_marker = Square(side_length=0.2, color=GREEN, fill_opacity=0.8)
            start_marker.move_to(start_pos)
            end_marker = Square(side_length=0.2, color=RED, fill_opacity=0.8)
            end_marker.move_to(end_pos)
            
            self.play(FadeIn(start_marker, end_marker))
            
            # 添加标签
            start_label = Text("起点", font_size=16, color=GREEN)
            start_label.next_to(start_marker, DOWN, buff=0.1)
            end_label = Text("终点", font_size=16, color=RED)
            end_label.next_to(end_marker, DOWN, buff=0.1)
            
            self.play(Write(start_label), Write(end_label))
            self.wait(1)
        
        # 7. 最终展示（停留几秒）
        self.wait(3)
        
        # 8. 淡出
        all_objects = [title, stats] + list(portal_dots.values()) + \
                     list(link_lines.values()) + list(field_polygons.values())
        if portal_labels:
            all_objects.extend(portal_labels.values())
        
        self.play(*[FadeOut(obj) for obj in all_objects], run_time=1)


class MultiAgentVisualization(Scene):
    """多人规划方案动画可视化场景"""
    
    def __init__(self, solution, planner: IngressPlanner, **kwargs):
        super().__init__(**kwargs)
        self.solution = solution
        self.planner = planner
        self.portal_positions = {}
        self._normalize_coordinates()
    
    def _normalize_coordinates(self):
        """将经纬度坐标归一化到屏幕坐标系"""
        all_portals = set()
        for agent_plan in self.solution.agent_plans:
            for link in agent_plan.links:
                all_portals.add(link.portal1)
                all_portals.add(link.portal2)
        
        if not all_portals:
            return
        
        lats = [p.lat for p in all_portals]
        lons = [p.lon for p in all_portals]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lon, max_lon = min(lons), max(lons)
        
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        range_lat = max_lat - min_lat if max_lat != min_lat else 0.01
        range_lon = max_lon - min_lon if max_lon != min_lon else 0.01
        
        scale = 5.0 / max(range_lat, range_lon * 0.7)
        
        for portal in all_portals:
            x = (portal.lon - center_lon) * scale * 0.7
            y = (portal.lat - center_lat) * scale
            self.portal_positions[portal] = np.array([x, y, 0])
    
    def get_portal_position(self, portal: Portal):
        """获取portal在屏幕上的位置"""
        return self.portal_positions.get(portal, ORIGIN)
    
    def construct(self):
        """构建多人规划动画场景"""
        num_agents = len(self.solution.agent_plans)
        colors = [BLUE, RED, GREEN, YELLOW, PURPLE, ORANGE, PINK, TEAL][:num_agents]
        
        # 标题
        title = Text(f"多人规划方案 ({num_agents}个Agent)", font_size=36)
        title.to_edge(UP)
        self.play(Write(title))
        
        # 统计信息
        stats_text = f"总AP: {self.solution.total_ap}"
        stats = Text(stats_text, font_size=24)
        stats.next_to(title, DOWN, buff=0.3)
        self.play(Write(stats))
        
        # 显示所有Portal
        all_portals = set()
        for agent_plan in self.solution.agent_plans:
            for link in agent_plan.links:
                all_portals.add(link.portal1)
                all_portals.add(link.portal2)
        
        portal_dots = {}
        for portal in all_portals:
            pos = self.get_portal_position(portal)
            dot = Dot(point=pos, radius=0.08, color=WHITE)
            portal_dots[portal] = dot
        
        self.play(*[FadeIn(dot) for dot in portal_dots.values()], lag_ratio=0.05)
        
        # 为每个Agent显示连接
        for agent_idx, agent_plan in enumerate(self.solution.agent_plans):
            color = colors[agent_idx]
            agent_label = Text(f"Agent {agent_idx + 1}: {agent_plan.ap} AP", 
                             font_size=20, color=color)
            agent_label.to_edge(DOWN).shift(UP * (0.5 + agent_idx * 0.3))
            
            if agent_idx == 0:
                self.play(Write(agent_label))
            else:
                self.play(Write(agent_label))
            
            # 显示该Agent的Links
            link_lines = []
            for link in agent_plan.links:
                p1_pos = self.get_portal_position(link.portal1)
                p2_pos = self.get_portal_position(link.portal2)
                line = Line(p1_pos, p2_pos, color=color, stroke_width=2.5)
                link_lines.append(line)
            
            if link_lines:
                self.play(*[Create(line) for line in link_lines], lag_ratio=0.1)
            
            # 显示路径
            if agent_plan.path and len(agent_plan.path) > 1:
                path_points = [self.get_portal_position(p) for p in agent_plan.path]
                path_line = VMobject()
                path_line.set_points_as_corners(path_points)
                path_line.set_stroke(color=color, width=2, opacity=0.6)
                path_line.set_stroke_dasharray([3, 3])
                self.play(Create(path_line), run_time=1)
            
            self.wait(0.5)
        
        self.wait(3)
        
        # 淡出
        all_objects = [title, stats] + list(portal_dots.values())
        self.play(*[FadeOut(obj) for obj in all_objects], run_time=1)


def create_animation(input_file: str, output_file: Optional[str] = None,
                    num_agents: int = 1, quality: str = "medium_quality",
                    show_labels: bool = True):
    """创建动画并渲染"""
    # 加载数据
    planner = IngressPlanner()
    planner.load_portals_from_file(input_file)
    
    # 生成方案
    if num_agents > 1:
        solution = planner.multi_agent_plan(num_agents=num_agents)
        scene_class = MultiAgentVisualization
        scene_kwargs = {"solution": solution, "planner": planner}
    else:
        solution = planner.plan()
        scene_class = IngressVisualization
        scene_kwargs = {"solution": solution, "planner": planner, 
                       "show_labels": show_labels}
    
    if not solution.links and not hasattr(solution, 'agent_plans'):
        print("错误：无法生成有效的连接方案")
        return
    
    # 创建场景
    scene = scene_class(**scene_kwargs)
    
    # 渲染（这里需要根据Manim的实际API调整）
    # 注意：Manim的渲染通常通过命令行完成
    print(f"方案已准备完成:")
    print(f"  总AP: {solution.total_ap if hasattr(solution, 'total_ap') else 'N/A'}")
    print(f"  请使用以下命令渲染:")
    print(f"  manim -pql {__file__} {scene_class.__name__}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='使用Manim创建Ingress可视化动画')
    parser.add_argument('--input', '-i', type=str, required=True,
                       help='输入Portal坐标文件')
    parser.add_argument('--output', '-o', type=str, 
                       help='输出视频文件（Manim会自动处理）')
    parser.add_argument('--agents', '-a', type=int, default=1,
                       help='Agent数量（多人规划）')
    parser.add_argument('--quality', '-q', type=str, default='medium_quality',
                       choices=['low_quality', 'medium_quality', 'high_quality'],
                       help='渲染质量')
    parser.add_argument('--no-labels', action='store_true',
                       help='不显示Portal标签')
    
    args = parser.parse_args()
    
    print("正在生成动画场景...")
    create_animation(args.input, args.output, args.agents, 
                    args.quality, not args.no_labels)
    print("\n提示：要渲染动画，请运行:")
    print(f"  manim -pql visualize_manim.py IngressVisualization")

