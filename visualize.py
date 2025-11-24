#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
可视化连接方案
"""

import matplotlib.pyplot as plt
import numpy as np
from planner import IngressPlanner, Solution, Link
from typing import Optional


def visualize_solution(planner: IngressPlanner, solution: Solution, 
                      output_file: Optional[str] = None, 
                      show_labels: bool = True):
    """可视化连接方案"""
    if not solution.links:
        print("没有连接方案可可视化")
        return
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # 绘制所有portal
    all_portals = set()
    for link in solution.links:
        all_portals.add(link.portal1)
        all_portals.add(link.portal2)
    
    portal_lats = [p.lat for p in all_portals]
    portal_lons = [p.lon for p in all_portals]
    
    # 绘制portal点
    ax.scatter(portal_lons, portal_lats, c='blue', s=100, 
              zorder=3, label='Portals')
    
    # 绘制links
    for link in solution.links:
        ax.plot([link.portal1.lon, link.portal2.lon],
               [link.portal1.lat, link.portal2.lat],
               'g-', linewidth=2, alpha=0.6, zorder=1)
    
    # 绘制fields（三角形）
    for field in solution.fields:
        triangle = np.array([
            [field.portal1.lon, field.portal1.lat],
            [field.portal2.lon, field.portal2.lat],
            [field.portal3.lon, field.portal3.lat],
            [field.portal1.lon, field.portal1.lat]  # 闭合
        ])
        ax.fill(triangle[:, 0], triangle[:, 1], 
               alpha=0.2, color='yellow', zorder=0)
    
    # 绘制路径
    if solution.path and len(solution.path) > 1:
        path_lons = [p.lon for p in solution.path]
        path_lats = [p.lat for p in solution.path]
        ax.plot(path_lons, path_lats, 'r--', linewidth=1.5, 
               alpha=0.8, zorder=2, label='路径')
        
        # 标记起点和终点
        ax.scatter([path_lons[0]], [path_lats[0]], 
                  c='green', s=150, marker='s', zorder=4, label='起点')
        ax.scatter([path_lons[-1]], [path_lats[-1]], 
                  c='red', s=150, marker='s', zorder=4, label='终点')
    
    # 添加标签
    if show_labels:
        for portal in all_portals:
            if portal.name:
                ax.annotate(portal.name, 
                          (portal.lon, portal.lat),
                          xytext=(5, 5), textcoords='offset points',
                          fontsize=8, alpha=0.7)
    
    ax.set_xlabel('经度')
    ax.set_ylabel('纬度')
    ax.set_title(f'Ingress连接方案\n总AP: {solution.total_ap}, '
                f'距离: {solution.distance/1000:.2f}km')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal', adjustable='box')
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"图像已保存到: {output_file}")
    else:
        plt.show()


def visualize_multi_agent(planner: IngressPlanner, solution, 
                         output_file: Optional[str] = None):
    """可视化多人规划方案"""
    import matplotlib.pyplot as plt
    import numpy as np
    
    num_agents = len(solution.agent_plans)
    colors = plt.cm.tab10(np.linspace(0, 1, num_agents))
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # 收集所有portal
    all_portals = set()
    for agent_plan in solution.agent_plans:
        for link in agent_plan.links:
            all_portals.add(link.portal1)
            all_portals.add(link.portal2)
    
    portal_lats = [p.lat for p in all_portals]
    portal_lons = [p.lon for p in all_portals]
    
    # 绘制portal点
    ax.scatter(portal_lons, portal_lats, c='black', s=100, zorder=3)
    
    # 为每个agent绘制不同的颜色
    for idx, agent_plan in enumerate(solution.agent_plans):
        color = colors[idx]
        label = f'Agent {idx} ({agent_plan.ap} AP)'
        
        # 绘制links
        for link in agent_plan.links:
            ax.plot([link.portal1.lon, link.portal2.lon],
                   [link.portal1.lat, link.portal2.lat],
                   color=color, linewidth=2, alpha=0.7, zorder=1)
        
        # 绘制路径
        if agent_plan.path and len(agent_plan.path) > 1:
            path_lons = [p.lon for p in agent_plan.path]
            path_lats = [p.lat for p in agent_plan.path]
            ax.plot(path_lons, path_lats, color=color, 
                   linewidth=1.5, linestyle='--', alpha=0.5, zorder=2)
    
    ax.set_xlabel('经度')
    ax.set_ylabel('纬度')
    ax.set_title(f'多人规划方案 (总AP: {solution.total_ap})')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal', adjustable='box')
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"图像已保存到: {output_file}")
    else:
        plt.show()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='可视化连接方案')
    parser.add_argument('--input', '-i', type=str, required=True,
                       help='Portal坐标文件')
    parser.add_argument('--output', '-o', type=str, help='输出图像文件')
    parser.add_argument('--agents', '-a', type=int, default=1,
                       help='Agent数量（多人规划）')
    
    args = parser.parse_args()
    
    planner = IngressPlanner()
    planner.load_portals_from_file(args.input)
    
    if args.agents > 1:
        solution = planner.multi_agent_plan(num_agents=args.agents)
        visualize_multi_agent(planner, solution, args.output)
    else:
        solution = planner.plan()
        visualize_solution(planner, solution, args.output)

