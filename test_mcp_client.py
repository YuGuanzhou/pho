#!/usr/bin/env python3
"""
MCP 客户端测试脚本
演示如何使用图片文字替换 MCP 服务器
"""

import asyncio
import base64
import json
import mcp.client.stdio
import mcp.types as types
from mcp.client.models import InitializationOptions

async def test_mcp_server():
    """测试 MCP 服务器功能"""
    
    # 连接到 MCP 服务器
    async with mcp.client.stdio.stdio_client(
        ["python", "mcp_server.py"]
    ) as (read_stream, write_stream):
        client = mcp.client.stdio.Client(
            read_stream,
            write_stream,
            InitializationOptions(
                client_name="test-client",
                client_version="1.0.0",
                capabilities={},
            ),
        )
        
        # 等待服务器初始化
        await client.initialize()
        
        print("=== 列出可用工具 ===")
        tools = await client.list_tools()
        for tool in tools:
            print(f"工具名称: {tool.name}")
            print(f"描述: {tool.description}")
            print(f"输入模式: {json.dumps(tool.inputSchema, indent=2, ensure_ascii=False)}")
            print("---")
        
        # 测试检测文字区域功能
        print("\n=== 测试检测文字区域 ===")
        try:
            # 读取测试图片并转换为 base64
            with open("test_image.jpg", "rb") as f:
                image_bytes = f.read()
                image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # 调用检测文字区域工具
            result = await client.call_tool(
                "detect_text_regions",
                {"image_data": image_b64}
            )
            
            print("检测结果:")
            for content in result:
                print(content.text)
                
        except Exception as e:
            print(f"检测文字区域时出错: {e}")
        
        # 测试文字替换功能
        print("\n=== 测试文字替换 ===")
        try:
            # 调用文字替换工具
            result = await client.call_tool(
                "replace_image_text",
                {
                    "image_data": image_b64,
                    "new_text": "这是替换后的中文文字",
                    "font_size": 40,
                    "output_format": "base64"
                }
            )
            
            print("替换结果:")
            for content in result:
                if "Base64 结果:" in content.text:
                    # 提取 base64 数据并保存
                    b64_data = content.text.split("Base64 结果:\n")[1]
                    output_bytes = base64.b64decode(b64_data)
                    with open("output_image.jpg", "wb") as f:
                        f.write(output_bytes)
                    print("图片已保存为 output_image.jpg")
                else:
                    print(content.text)
                    
        except Exception as e:
            print(f"文字替换时出错: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_server()) 