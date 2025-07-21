#!/bin/bash

# 智能体评估系统启动脚本

echo "==================================="
echo "    智能体评估系统启动脚本"
echo "==================================="

# 检查Python版本
echo "检查Python版本..."
python --version

# 检查依赖
echo "检查依赖包..."
if [ ! -f "requirements.txt" ]; then
    echo "错误: 找不到requirements.txt文件"
    exit 1
fi

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p uploads
mkdir -p outputs
mkdir -p static/css
mkdir -p static/js
mkdir -p templates

# 启动应用
echo "启动智能体评估系统..."
echo "访问地址: http://localhost:12000"
echo "按 Ctrl+C 停止服务"
echo "==================================="

python app.py