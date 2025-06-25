@echo off
chcp 65001
echo 启动图片文字替换 MCP 服务器...
echo.
echo 确保已安装依赖包：
echo pip install -r requirements.txt
echo.
echo 按任意键继续...
pause >nul

python mcp_server.py

echo.
echo MCP 服务器已停止
pause 