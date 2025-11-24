#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试规划器功能（带可视化）
"""

from planner import IngressPlanner, Portal, Link, FIELD_AP
from visualize import visualize_solution, visualize_multi_agent
import os


def test_basic_planning():
    """测试基本规划功能"""
    print("=" * 60)
    print("测试1: 基本规划功能")
    print("=" * 60)
    
    planner = IngressPlanner()
    
    # 添加示例portal
    portals = [
        (40.008008, 116.327477),
        (40.008102, 116.326605),
        (40.008034, 116.325578),
        (40.008151, 116.327164),
        (40.008393, 116.326263),
    ]
    
    for lat, lon in portals:
        planner.add_portal(lat, lon)
    
    solution = planner.plan()
    print(solution)
    print()
    
    # 生成可视化
    output_file = 'test_visual_basic.png'
    visualize_solution(planner, solution, output_file)
    print(f"✅ 可视化图像已保存: {output_file}\n")


def test_file_loading():
    """测试从文件加载portal"""
    print("=" * 60)
    print("测试2: 从文件加载Portal")
    print("=" * 60)
    
    planner = IngressPlanner()
    planner.load_portals_from_file('example_portals.txt')
    
    print(f"加载了 {len(planner.portals)} 个Portal:")
    for portal in planner.portals:
        print(f"  {portal.name or f'Portal{portal.id}'}: "
              f"({portal.lat}, {portal.lon})")
    print()
    
    # 生成规划方案并可视化
    solution = planner.plan()
    output_file = 'test_visual_file_loading.png'
    visualize_solution(planner, solution, output_file)
    print(f"✅ 可视化图像已保存: {output_file}\n")


def test_multi_agent():
    """测试多人规划"""
    print("=" * 60)
    print("测试3: 多人规划")
    print("=" * 60)
    
    planner = IngressPlanner()
    planner.load_portals_from_file('example_portals.txt')
    
    solution = planner.multi_agent_plan(num_agents=3)
    print(solution)
    print()
    
    # 生成可视化
    output_file = 'test_visual_multi_agent.png'
    visualize_multi_agent(planner, solution, output_file)
    print(f"✅ 可视化图像已保存: {output_file}\n")


def test_ap_calculation():
    """测试AP计算"""
    print("=" * 60)
    print("测试4: AP值计算")
    print("=" * 60)
    
    planner = IngressPlanner()
    
    # 创建测试portal
    p1 = planner.add_portal(40.008008, 116.327477, "Portal1")
    p2 = planner.add_portal(40.008102, 116.326605, "Portal2")
    
    # 计算距离和AP
    distance = planner._calculate_distance(p1, p2)
    link = Link(p1, p2, distance)
    
    print(f"Portal1 -> Portal2:")
    print(f"  距离: {distance:.2f} 米 ({distance/1000:.2f} 公里)")
    print(f"  Link AP: {link.ap}")
    print(f"  Field AP: {FIELD_AP}")
    print()


if __name__ == '__main__':
    try:
        print("\n" + "="*60)
        print("IngressPlanner 测试（带可视化）")
        print("="*60 + "\n")
        
        test_basic_planning()
        test_file_loading()
        test_multi_agent()
        test_ap_calculation()
        
        print("=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        print("\n生成的可视化文件：")
        visual_files = [
            'test_visual_basic.png',
            'test_visual_file_loading.png',
            'test_visual_multi_agent.png'
        ]
        for f in visual_files:
            if os.path.exists(f):
                print(f"  - {f}")
        print()
        
    except Exception as e:
        print(f"测试出错: {e}")
        import traceback
        traceback.print_exc()

