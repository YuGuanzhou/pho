#!/usr/bin/env python3
"""
图片文字替换 MCP 服务器
这个服务器提供工具来移除图片中的文字并用新文字替换
"""

import asyncio
import base64
import io
import json
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional, Sequence
from pathlib import Path

import mcp.server
import mcp.server.stdio
import mcp.types as types
from mcp.server.models import InitializationOptions

from replace_text_in_image import remove_text_and_replace
import easyocr

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局初始化 EasyOCR 读取器
reader = None

def get_easyocr_reader():
    """获取或创建 EasyOCR 读取器实例"""
    global reader
    if reader is None:
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    return reader

class ImageTextReplacementServer:
    """图片文字替换 MCP 服务器"""
    
    def __init__(self):
        self.server = mcp.server.Server("image-text-replacement")
        
        # 注册工具
        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)
        
        # 注册资源
        self.server.list_resources()(self.list_resources)
        self.server.read_resource()(self.read_resource)
    
    async def list_tools(self) -> List[types.Tool]:
        """列出可用工具"""
        return [
            types.Tool(
                name="replace_image_text",
                description="移除图片中的文字并用新的翻译文字替换",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_data": {
                            "type": "string",
                            "description": "Base64编码的图片数据或图片文件路径"
                        },
                        "new_text": {
                            "type": "string",
                            "description": "用于替换原图片文字的新文字"
                        },
                        "font_path": {
                            "type": "string",
                            "description": "可选的自定义字体文件路径（TTF格式）",
                            "default": None
                        },
                        "font_size": {
                            "type": "integer",
                            "description": "新文字的字体大小",
                            "default": 32
                        },
                        "output_format": {
                            "type": "string",
                            "description": "输出格式：'base64' 或 'file'",
                            "enum": ["base64", "file"],
                            "default": "base64"
                        }
                    },
                    "required": ["image_data", "new_text"]
                }
            ),
            types.Tool(
                name="detect_text_regions",
                description="检测图片中的文字区域（不进行替换）",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "image_data": {
                            "type": "string",
                            "description": "Base64编码的图片数据或图片文件路径"
                        }
                    },
                    "required": ["image_data"]
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """调用特定工具"""
        try:
            if name == "replace_image_text":
                return await self._replace_image_text(arguments)
            elif name == "detect_text_regions":
                return await self._detect_text_regions(arguments)
            else:
                raise ValueError(f"未知工具: {name}")
        except Exception as e:
            logger.error(f"调用工具 {name} 时出错: {e}")
            return [types.TextContent(
                type="text",
                text=f"错误: {str(e)}"
            )]
    
    async def _replace_image_text(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """用新文字替换图片中的文字"""
        image_data = arguments["image_data"]
        new_text = arguments["new_text"]
        font_path = arguments.get("font_path")
        font_size = arguments.get("font_size", 32)
        output_format = arguments.get("output_format", "base64")
        
        # 处理图片输入
        if image_data.startswith("data:image") or len(image_data) > 200:
            # Base64编码的图片
            try:
                if image_data.startswith("data:image"):
                    # 移除 data URL 前缀
                    image_data = image_data.split(",", 1)[1]
                image_bytes = base64.b64decode(image_data)
                input_image = io.BytesIO(image_bytes)
            except Exception as e:
                raise ValueError(f"无效的 base64 图片数据: {e}")
        else:
            # 文件路径
            if not os.path.exists(image_data):
                raise FileNotFoundError(f"找不到图片文件: {image_data}")
            input_image = image_data
        
        # 创建临时输出文件
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_output:
            output_path = temp_output.name
        
        try:
            # 获取 EasyOCR 读取器
            reader = get_easyocr_reader()
            
            # 处理图片
            remove_text_and_replace(
                input_image, 
                new_text, 
                output_path, 
                font_path, 
                font_size, 
                reader=reader
            )
            
            # 根据输出格式返回结果
            if output_format == "base64":
                with open(output_path, "rb") as f:
                    output_bytes = f.read()
                output_b64 = base64.b64encode(output_bytes).decode('utf-8')
                return [types.TextContent(
                    type="text",
                    text=f"图片处理成功。Base64 结果:\n{output_b64}"
                )]
            else:
                return [types.TextContent(
                    type="text",
                    text=f"图片处理成功。输出保存到: {output_path}"
                )]
                
        finally:
            # 如果是 base64 输出，清理临时文件
            if output_format == "base64" and os.path.exists(output_path):
                os.unlink(output_path)
    
    async def _detect_text_regions(self, arguments: Dict[str, Any]) -> List[types.TextContent]:
        """检测图片中的文字区域"""
        image_data = arguments["image_data"]
        
        # 处理图片输入
        if image_data.startswith("data:image") or len(image_data) > 200:
            # Base64编码的图片
            try:
                if image_data.startswith("data:image"):
                    # 移除 data URL 前缀
                    image_data = image_data.split(",", 1)[1]
                image_bytes = base64.b64decode(image_data)
                input_image = io.BytesIO(image_bytes)
            except Exception as e:
                raise ValueError(f"无效的 base64 图片数据: {e}")
        else:
            # 文件路径
            if not os.path.exists(image_data):
                raise FileNotFoundError(f"找不到图片文件: {image_data}")
            input_image = image_data
        
        try:
            from PIL import Image
            from replace_text_in_image import fast_ocr
            
            # 加载图片
            if isinstance(input_image, str):
                image = Image.open(input_image)
            else:
                image = Image.open(input_image)
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # 获取 EasyOCR 读取器
            reader = get_easyocr_reader()
            
            # 检测文字区域
            rects = fast_ocr(image, reader)
            
            # 格式化结果
            result = {
                "detected_regions": len(rects),
                "regions": [
                    {
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h
                    }
                    for x, y, w, h in rects
                ]
            }
            
            return [types.TextContent(
                type="text",
                text=f"检测到 {len(rects)} 个文字区域:\n{json.dumps(result, indent=2, ensure_ascii=False)}"
            )]
            
        except Exception as e:
            raise ValueError(f"检测文字区域时出错: {e}")
    
    async def list_resources(self) -> List[types.Resource]:
        """列出可用资源"""
        return []
    
    async def read_resource(self, uri: str) -> types.ReadResourceResult:
        """读取资源"""
        raise ValueError(f"找不到资源: {uri}")

async def main():
    """主入口点"""
    # 创建服务器实例
    server = ImageTextReplacementServer()
    
    # 运行服务器
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="image-text-replacement",
                server_version="1.0.0",
                capabilities=server.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())