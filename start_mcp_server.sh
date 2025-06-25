#!/bin/bash

echo "启动图片文字替换 MCP 服务器..."
echo ""
echo "确保已安装依赖包："
echo "pip install -r requirements.txt"
echo ""

# 检查Python是否安装
if ! command -v python &> /dev/null; then
    echo "错误: 未找到 Python，请先安装 Python"
    exit 1
fi

# 检查依赖包是否安装
if ! python -c "import mcp" &> /dev/null; then
    echo "警告: 未找到 mcp 包，请运行: pip install -r requirements.txt"
    echo "是否继续？(y/n)"
    read -r response
    if [[ "$response" != "y" && "$response" != "Y" ]]; then
        exit 1
    fi
fi

echo "启动 MCP 服务器..."
python mcp_server.py

echo ""
echo "MCP 服务器已停止" 