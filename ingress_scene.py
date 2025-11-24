#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Manim场景类：用于直接渲染Ingress动画
使用方式: manim -pql ingress_scene.py IngressScene
"""

from manim import *
import numpy as np
import sys
import os

# 添加当前目录到路径，以便导入planner模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from planner import IngressPlanner, Solution, Portal, Link, Field


class IngressScene(Scene):
    """Ingress连接方案动画场景 - 可被Manim直接调用"""
    
    CONFIG = {
        "input_file": "example_portals.txt",
        "show_labels": True,
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.planner = IngressPlanner()
        self.solution = None
        self.portal_positions = {}
        
        # 优先使用环境变量或命令行参数指定的文件
        input_file = (
            os.environ.get('INGRESS_INPUT_FILE') or
            kwargs.get('input_file') or
            self.CONFIG.get('input_file', 'example_portals.txt')
        )
        
        # 尝试多个可能的文件位置
        possible_files = [
            input_file,
            os.path.join(os.path.dirname(__file__), input_file),
            os.path.join(os.path.dirname(__file__), 'example_portals.txt'),
            os.path.join(os.path.dirname(__file__), 'portals_zijing.txt'),
        ]
        
        file_found = False
        for file_path in possible_files:
            if os.path.exists(file_path):
                try:
                    self.planner.load_portals_from_file(file_path)
                    self.solution = self.planner.plan()
                    self._normalize_coordinates()
                    file_found = True
                    print(f"✓ 成功加载Portal文件: {file_path}")
                    break
                except Exception as e:
                    print(f"警告：加载文件 {file_path} 时出错: {e}")
                    continue
        
        if not file_found:
            print("警告：未找到Portal文件，使用示例数据")
            self._load_example_data()
    
    def _load_example_data(self):
        """加载示例数据"""
        example_portals = [
            (40.008008, 116.327477),
            (40.008102, 116.326605),
            (40.008034, 116.325578),
            (40.008151, 116.327164),
            (40.008393, 116.326263),
        ]
        for lat, lon in example_portals:
            self.planner.add_portal(lat, lon)
        self.solution = self.planner.plan()
        self._normalize_coordinates()
    
    def _normalize_coordinates(self):
        """将经纬度坐标归一化到屏幕坐标系"""
        if not self.solution or not self.solution.links:
            return
        
        all_portals = set()
        for link in self.solution.links:
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
        
        # 计算缩放比例，适应Manim的坐标系（-7到7的范围）
        scale = 5.0 / max(range_lat, range_lon * 0.7)
        
        for portal in all_portals:
            x = (portal.lon - center_lon) * scale * 0.7
            y = (portal.lat - center_lat) * scale
            self.portal_positions[portal] = np.array([x, y, 0])
    
    def get_portal_position(self, portal: Portal):
        """获取portal在屏幕上的位置"""
        return self.portal_positions.get(portal, ORIGIN)
    
    def construct(self):
        """构建动画场景"""
        if not self.solution or not self.solution.links:
            text = Text("没有连接方案可展示", font_size=48)
            self.play(Write(text))
            self.wait(2)
            return
        
        # 1. 标题
        title = Text("Ingress 多重控制场规划方案", 
                    font_size=40, color=BLUE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1)
        self.wait(0.5)
        
        # 2. 显示统计信息
        stats_text = (
            f"总AP: {self.solution.total_ap}  |  "
            f"Links: {len(self.solution.links)}  |  "
            f"Fields: {len(self.solution.fields)}  |  "
            f"距离: {self.solution.distance/1000:.2f}km"
        )
        stats = Text(stats_text, font_size=24, color=WHITE)
        stats.next_to(title, DOWN, buff=0.4)
        self.play(Write(stats), run_time=1)
        self.wait(0.5)
        
        # 3. 显示所有Portal点
        portal_dots = {}
        portal_labels = {}
        all_portals = set()
        
        for link in self.solution.links:
            all_portals.add(link.portal1)
            all_portals.add(link.portal2)
        
        # 创建portal点和标签
        portal_objects = []
        for portal in all_portals:
            pos = self.get_portal_position(portal)
            # 创建带外圈的portal点
            outer_circle = Circle(radius=0.15, color=BLUE, stroke_width=2)
            inner_dot = Dot(point=pos, radius=0.08, color=BLUE, fill_opacity=1)
            portal_group = VGroup(outer_circle, inner_dot)
            portal_group.move_to(pos)
            portal_dots[portal] = portal_group
            portal_objects.append(portal_group)
            
            if self.CONFIG.get('show_labels', True) and portal.name:
                label = Text(portal.name, font_size=14, color=WHITE)
                label.next_to(portal_group, UR, buff=0.15)
                portal_labels[portal] = label
                portal_objects.append(label)
        
        # 动画显示portal
        self.play(*[FadeIn(obj, scale=0.8) for obj in portal_objects], 
                 lag_ratio=0.15, run_time=2)
        self.wait(0.5)
        
        # 4. 逐步显示Links（带动画效果）
        link_lines = {}
        link_animations = []
        
        for i, link in enumerate(self.solution.links):
            p1_pos = self.get_portal_position(link.portal1)
            p2_pos = self.get_portal_position(link.portal2)
            line = Line(p1_pos, p2_pos, color=GREEN, stroke_width=4)
            link_lines[link] = line
            
            # 添加AP标签（小字体显示在中间）
            mid_point = (p1_pos + p2_pos) / 2
            ap_label = Text(str(link.ap), font_size=12, color=GREEN_C)
            ap_label.move_to(mid_point + UP * 0.15)
            
            link_group = VGroup(line, ap_label)
            link_animations.append(
                AnimationGroup(
                    Create(line),
                    FadeIn(ap_label, scale=0.3),
                    lag_ratio=0.2
                )
            )
        
        # 逐步创建links
        self.play(*link_animations, lag_ratio=0.15, run_time=3)
        self.wait(0.8)
        
        # 5. 显示Fields（三角形填充，带淡入效果）
        if self.solution.fields:
            field_polygons = []
            field_animations = []
            
            for field in self.solution.fields:
                p1_pos = self.get_portal_position(field.portal1)
                p2_pos = self.get_portal_position(field.portal2)
                p3_pos = self.get_portal_position(field.portal3)
                
                polygon = Polygon(p1_pos, p2_pos, p3_pos, 
                                fill_opacity=0.25, fill_color=YELLOW,
                                stroke_width=1.5, stroke_color=YELLOW_C)
                field_polygons.append(polygon)
                field_animations.append(
                    FadeIn(polygon, scale=0.5, run_time=0.8)
                )
            
            self.play(*field_animations, lag_ratio=0.1, run_time=2)
            self.wait(0.5)
        
        # 6. 显示路径（如果存在，带动态绘制效果）
        if self.solution.path and len(self.solution.path) > 1:
            path_title = Text("行走路径", font_size=28, color=RED)
            path_title.to_edge(DOWN, buff=0.3)
            self.play(Write(path_title))
            self.wait(0.3)
            
            path_points = [self.get_portal_position(p) for p in self.solution.path]
            
            # 创建路径线
            path_line = VMobject()
            path_line.set_points_as_corners(path_points)
            path_line.set_stroke(color=RED, width=3, opacity=0.9)
            path_line.set_stroke_dasharray([8, 4])
            
            # 动态绘制路径
            self.play(Create(path_line), run_time=2.5)
            
            # 标记起点和终点
            start_pos = self.get_portal_position(self.solution.path[0])
            end_pos = self.get_portal_position(self.solution.path[-1])
            
            start_marker = Square(side_length=0.25, color=GREEN, 
                                fill_opacity=0.9, stroke_width=2)
            start_marker.move_to(start_pos)
            
            end_marker = Square(side_length=0.25, color=RED, 
                              fill_opacity=0.9, stroke_width=2)
            end_marker.move_to(end_pos)
            
            start_label = Text("起点", font_size=16, color=GREEN)
            start_label.next_to(start_marker, DOWN, buff=0.15)
            end_label = Text("终点", font_size=16, color=RED)
            end_label.next_to(end_marker, DOWN, buff=0.15)
            
            self.play(
                FadeIn(start_marker, scale=0.5),
                FadeIn(end_marker, scale=0.5),
                Write(start_label),
                Write(end_label),
                run_time=1
            )
            self.wait(1)
        
        # 7. 最终展示（停留）
        self.wait(2)
        
        # 8. 淡出所有元素
        all_objects = [title, stats]
        all_objects.extend(portal_dots.values())
        if portal_labels:
            all_objects.extend(portal_labels.values())
        all_objects.extend(link_lines.values())
        if self.solution.fields:
            all_objects.extend([p for p in self.portal_positions.values()])
        
        self.play(*[FadeOut(obj) for obj in all_objects if obj in self.mobjects], 
                 run_time=1.5)


class MultiAgentScene(Scene):
    """多人规划方案动画场景"""
    
    CONFIG = {
        "input_file": "example_portals.txt",
        "num_agents": 3,
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.planner = IngressPlanner()
        self.solution = None
        self.portal_positions = {}
        
        # 优先使用环境变量
        input_file = (
            os.environ.get('INGRESS_INPUT_FILE') or
            kwargs.get('input_file') or
            self.CONFIG.get('input_file', 'example_portals.txt')
        )
        num_agents = int(
            os.environ.get('INGRESS_NUM_AGENTS') or
            kwargs.get('num_agents') or
            self.CONFIG.get('num_agents', 3)
        )
        
        # 尝试多个可能的文件位置
        possible_files = [
            input_file,
            os.path.join(os.path.dirname(__file__), input_file),
            os.path.join(os.path.dirname(__file__), 'example_portals.txt'),
            os.path.join(os.path.dirname(__file__), 'portals_zijing.txt'),
        ]
        
        file_found = False
        for file_path in possible_files:
            if os.path.exists(file_path):
                try:
                    self.planner.load_portals_from_file(file_path)
                    self.solution = self.planner.multi_agent_plan(num_agents=num_agents)
                    self._normalize_coordinates()
                    file_found = True
                    print(f"✓ 成功加载Portal文件: {file_path} (Agent数: {num_agents})")
                    break
                except Exception as e:
                    print(f"警告：加载文件 {file_path} 时出错: {e}")
                    continue
        
        if not file_found:
            print(f"警告：未找到Portal文件，使用示例数据 (Agent数: {num_agents})")
            self._load_example_data(num_agents)
    
    def _load_example_data(self, num_agents=3):
        """加载示例数据"""
        example_portals = [
            (40.008008, 116.327477),
            (40.008102, 116.326605),
            (40.008034, 116.325578),
            (40.008151, 116.327164),
            (40.008393, 116.326263),
            (40.008131, 116.326011),
            (40.008129, 116.326349),
        ]
        for lat, lon in example_portals:
            self.planner.add_portal(lat, lon)
        self.solution = self.planner.multi_agent_plan(num_agents=num_agents)
        self._normalize_coordinates()
    
    def _normalize_coordinates(self):
        """将经纬度坐标归一化到屏幕坐标系"""
        if not self.solution or not self.solution.agent_plans:
            return
        
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
        if not self.solution or not self.solution.agent_plans:
            text = Text("没有规划方案可展示", font_size=48)
            self.play(Write(text))
            self.wait(2)
            return
        
        num_agents = len(self.solution.agent_plans)
        colors = [BLUE, RED, GREEN, YELLOW, PURPLE, ORANGE, PINK, TEAL][:num_agents]
        
        # 标题
        title = Text(f"多人规划方案 ({num_agents}个Agent)", 
                    font_size=36, color=BLUE)
        title.to_edge(UP, buff=0.5)
        self.play(Write(title))
        
        # 统计信息
        stats_text = f"总AP: {self.solution.total_ap}"
        stats = Text(stats_text, font_size=28, color=WHITE)
        stats.next_to(title, DOWN, buff=0.4)
        self.play(Write(stats))
        
        # 显示所有Portal
        all_portals = set()
        for agent_plan in self.solution.agent_plans:
            for link in agent_plan.links:
                all_portals.add(link.portal1)
                all_portals.add(link.portal2)
        
        portal_dots = []
        for portal in all_portals:
            pos = self.get_portal_position(portal)
            outer_circle = Circle(radius=0.12, color=WHITE, stroke_width=2)
            inner_dot = Dot(point=pos, radius=0.06, color=WHITE)
            portal_group = VGroup(outer_circle, inner_dot)
            portal_group.move_to(pos)
            portal_dots.append(portal_group)
        
        self.play(*[FadeIn(dot, scale=0.8) for dot in portal_dots], 
                 lag_ratio=0.05, run_time=1.5)
        self.wait(0.3)
        
        # 为每个Agent显示连接
        for agent_idx, agent_plan in enumerate(self.solution.agent_plans):
            color = colors[agent_idx]
            
            # Agent信息
            agent_info = (
                f"Agent {agent_idx + 1}: "
                f"{agent_plan.ap} AP | "
                f"{len(agent_plan.links)} Links | "
                f"{agent_plan.distance/1000:.2f}km"
            )
            agent_label = Text(agent_info, font_size=18, color=color)
            agent_label.to_edge(DOWN, buff=0.5).shift(
                UP * (0.2 + (num_agents - 1 - agent_idx) * 0.4)
            )
            
            self.play(Write(agent_label), run_time=0.8)
            
            # 显示该Agent的Links
            link_lines = []
            for link in agent_plan.links:
                p1_pos = self.get_portal_position(link.portal1)
                p2_pos = self.get_portal_position(link.portal2)
                line = Line(p1_pos, p2_pos, color=color, stroke_width=3)
                link_lines.append(line)
            
            if link_lines:
                self.play(*[Create(line) for line in link_lines], 
                         lag_ratio=0.1, run_time=1.5)
            
            # 显示该Agent的Fields
            field_polygons = []
            for field in agent_plan.fields:
                p1_pos = self.get_portal_position(field.portal1)
                p2_pos = self.get_portal_position(field.portal2)
                p3_pos = self.get_portal_position(field.portal3)
                polygon = Polygon(p1_pos, p2_pos, p3_pos, 
                                fill_opacity=0.15, fill_color=color,
                                stroke_width=1, stroke_color=color)
                field_polygons.append(polygon)
            
            if field_polygons:
                self.play(*[FadeIn(poly, scale=0.5) for poly in field_polygons],
                         lag_ratio=0.1, run_time=1)
            
            # 显示路径
            if agent_plan.path and len(agent_plan.path) > 1:
                path_points = [self.get_portal_position(p) 
                             for p in agent_plan.path]
                path_line = VMobject()
                path_line.set_points_as_corners(path_points)
                path_line.set_stroke(color=color, width=2.5, opacity=0.7)
                path_line.set_stroke_dasharray([5, 3])
                self.play(Create(path_line), run_time=1.2)
            
            self.wait(0.5)
        
        self.wait(3)
        
        # 淡出
        all_objects = [title, stats, agent_label] + portal_dots
        self.play(*[FadeOut(obj) for obj in all_objects if obj in self.mobjects], 
                 run_time=1.5)

