#!/bin/bash
# Ingress动画渲染脚本

# 使用方法：
# ./render_animation.sh [场景名] [输入文件] [Agent数量] [质量]
# 示例：
# ./render_animation.sh IngressScene portals_zijing.txt 1 high
# ./render_animation.sh MultiAgentScene portals_zijing.txt 3 medium

SCENE=${1:-IngressScene}
INPUT_FILE=${2:-example_portals.txt}
NUM_AGENTS=${3:-3}
QUALITY=${4:-medium}

# 设置质量参数
case $QUALITY in
    low|l)
        QUALITY_FLAG="-ql"
        ;;
    medium|m)
        QUALITY_FLAG="-qm"
        ;;
    high|h)
        QUALITY_FLAG="-qh"
        ;;
    *)
        QUALITY_FLAG="-qm"
        ;;
esac

echo "========================================="
echo "Ingress动画渲染"
echo "========================================="
echo "场景: $SCENE"
echo "输入文件: $INPUT_FILE"
echo "Agent数量: $NUM_AGENTS"
echo "质量: $QUALITY ($QUALITY_FLAG)"
echo "========================================="

# 设置环境变量
export INGRESS_INPUT_FILE="$INPUT_FILE"
export INGRESS_NUM_AGENTS="$NUM_AGENTS"

# 渲染动画
manim -p $QUALITY_FLAG ingress_scene.py $SCENE

echo ""
echo "✓ 渲染完成！"
echo "视频位置: media/videos/ingress_scene/"

