#!/usr/bin/env python3
"""
测试示例：展示如何使用 replace_text_in_image 函数
"""

import os
from replace_text_in_image import remove_text_and_replace

def test_with_sample():
    """测试函数调用方式"""
    
    # 检查是否有测试图片
    test_image = "test_image.jpg"  # 你可以替换为你的图片路径
    
    if not os.path.exists(test_image):
        print(f"请将测试图片命名为 '{test_image}' 或修改代码中的图片路径")
        print("或者使用命令行方式：")
        print("python replace_text_in_image.py --image your_image.jpg --text '新文字' --output result.jpg")
        return
    
    try:
        # 调用函数
        remove_text_and_replace(
            image_path=test_image,
            new_text="test",
            output_path="output_result.jpg",
            font_path=None,  # 使用默认字体
            font_size=32
        )
        print("测试完成！请查看 output_result.jpg")
        
    except Exception as e:
        print(f"测试失败: {e}")
        print("请确保：")
        print("1. 已安装所有依赖: pip install -r requirements.txt")
        print("2. 图片路径正确且图片包含文字")

if __name__ == "__main__":
     test_with_sample()