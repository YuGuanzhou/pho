# 图片文字去除与替换工具（EasyOCR版）

## 简介
本工具基于 EasyOCR 和 Pillow，无需 Tesseract，支持中英文图片中的文字自动检测、去除和替换。适用于批量处理带有水印、标语、说明等文字的图片，或为AI自动化流程提供图片文字编辑能力。

## 主要特性
- **无需Tesseract**，纯Python依赖，安装简单
- **自动检测图片中的文字区域**（支持中英文）
- **多边形遮罩+模糊/填充**，智能去除原文字
- **支持自定义新文字内容、字体、字号**
- **命令行和Python两种调用方式**
- **可选MCP服务器模式**，便于AI应用集成

## 安装依赖

```bash
pip install -r requirements.txt
```

> 依赖：Pillow<10.0.0、easyocr>=1.7.0、numpy>=1.19.0、torch>=1.9.0

## 使用方法

### 1. 命令行方式

```bash
python replace_text_in_image.py --image 输入图片.jpg --text "新文字" --output 输出图片.jpg --font 字体文件.ttf --fontsize 32
```

**参数说明：**
- `--image`：输入图片路径（必需）
- `--text`：要写入的新文字（必需）
- `--output`：输出图片路径（必需）
- `--font`：字体文件路径（可选，如 simhei.ttf，推荐指定支持中文的字体）
- `--fontsize`：字体大小（可选，默认32）

### 2. Python调用

```python
from replace_text_in_image import remove_text_and_replace
import easyocr

# 创建 EasyOCR 读取器（可选，函数内部会自动创建）
reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)

remove_text_and_replace(
    image_path='输入图片.jpg',
    new_text='新文字',
    output_path='输出图片.jpg',
    font_path='simhei.ttf',  # 可选
    font_size=32,            # 可选，默认32
    reader=reader            # 可选，默认None
)
```

### 3. MCP服务器模式（仅供AI应用集成，普通用户可忽略）

本项目包含 `mcp_server.py`，可作为 MCP (Model Context Protocol) 服务器，供支持 MCP 协议的 AI 应用（如 Claude Desktop）集成调用。

#### 启动 MCP 服务器

```bash
python mcp_server.py
```

启动后会显示：
```
MCP 服务器已启动，等待客户端连接...
```

#### 典型集成场景
- 由 AI 应用（如 Claude Desktop）通过 MCP 协议调用本服务器，实现图片文字去除与替换自动化。
- 服务器本身不提供命令行参数调用或 HTTP API。

#### MCP服务器参数说明（供AI开发者参考）
- `replace_image_text`：移除图片中的文字并用新文字替换
- `detect_text_regions`：检测图片中的文字区域（不进行替换）

## 常见问题
- **中文字体显示异常？** 请指定支持中文的.ttf字体（如 simhei.ttf、msyh.ttc）
- **部分文字未完全去除？** 受限于OCR检测精度和图片复杂度，可尝试更换图片、调整参数或手动辅助
- **依赖安装失败？** 请确保Python 3.7+，pip已升级，国内可用镜像源加速
- **MCP服务器连接失败？** 仅AI应用开发者需关注，普通用户无需理会

## 文件结构
```
pho/
├── replace_text_in_image.py    # 核心功能模块
├── mcp_server.py              # MCP服务器（仅供AI应用集成）
├── mcp_config.json            # MCP配置文件（仅供AI应用集成）
├── requirements.txt           # 依赖包列表
├── test_image.jpg             # 测试图片
├── start_mcp_server.bat       # Windows启动脚本
├── start_mcp_server.sh        # Linux/Mac启动脚本
└── README.md                  # 说明文档
```

---

如有更多需求或遇到问题，欢迎反馈！ 