# 图片文字去除与替换工具（EasyOCR版）

## 简介
本工具基于 EasyOCR 和 Pillow，无需 Tesseract，支持中英文图片中的文字自动检测、去除和替换。适用于批量处理带有水印、标语、说明等文字的图片，或为AI自动化流程提供图片文字编辑能力。

## 主要特性
- **无需Tesseract**，纯Python依赖，安装简单
- **自动检测图片中的文字区域**（支持中英文）
- **多边形遮罩+模糊/填充**，智能去除原文字
- **支持自定义新文字内容、字体、字号**
- **命令行和Python两种调用方式**

## 安装依赖

```bash
pip install -r requirements.txt
```

> 依赖：easyocr、Pillow、numpy、torch（EasyOCR自动安装）

## 使用方法

### 1. 命令行方式

```bash
python replace_text_in_image.py --image 输入图片.jpg --text "新文字" --output 输出图片.jpg --font 字体文件.ttf
```

**参数说明：**
- `--image`：输入图片路径
- `--text`：要写入的新文字
- `--output`：输出图片路径
- `--font`：字体文件路径（如 simhei.ttf，推荐指定支持中文的字体）
- `--fontsize`：字体大小（可选，默认32）

### 2. Python调用

```python
from replace_text_in_image import remove_text_and_replace
remove_text_and_replace(
    image_path='输入图片.jpg',
    new_text='新文字',
    output_path='输出图片.jpg',
    font_path='simhei.ttf',
    font_size=32
)
```

## 功能流程说明
1. **自动检测图片中的文字区域**（EasyOCR，返回多边形）
2. **对检测到的区域做多边形遮罩+模糊/填充**，最大程度去除原文字
3. **在原位置写入新文字**，支持自适应字号、描边、颜色自定义

## 效果说明
- 适合背景较为均匀、文字与背景对比明显的图片
- 对复杂背景、低对比度、雾气/光晕等情况，自动检测和去除效果有限
- 遮罩为多边形，边缘羽化，尽量自然
- 新文字可自定义字体、颜色、描边

## 常见问题
- **中文字体显示异常？** 请指定支持中文的.ttf字体（如 simhei.ttf、msyh.ttc）
- **部分文字未完全去除？** 受限于OCR检测精度和图片复杂度，可尝试更换图片、调整参数或手动辅助
- **依赖安装失败？** 请确保Python 3.7+，pip已升级，国内可用镜像源加速

## 适用场景与局限性
- 适合批量去除/替换图片中的水印、标语、说明等
- 不适合极其复杂背景、艺术字、极低对比度等极端场景
- 若需更高精度，建议结合手动辅助或专业修图工具

---

如有更多定制需求或遇到特殊问题，欢迎反馈！ 