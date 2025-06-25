# 图片文字去除与替换工具（EasyOCR版）

## 简介
本工具基于 EasyOCR 和 Pillow，无需 Tesseract，支持中英文图片中的文字自动检测、去除和替换。适用于批量处理带有水印、标语、说明等文字的图片，或为AI自动化流程提供图片文字编辑能力。

**新增功能：** 现已支持 MCP (Model Context Protocol) 服务器模式，可以轻松集成到支持 MCP 的 AI 应用中。

## 主要特性
- **无需Tesseract**，纯Python依赖，安装简单
- **自动检测图片中的文字区域**（支持中英文）
- **多边形遮罩+模糊/填充**，智能去除原文字
- **支持自定义新文字内容、字体、字号**
- **命令行和Python两种调用方式**
- **MCP服务器模式**，支持AI应用集成

## 安装依赖

```bash
pip install -r requirements.txt
```

> 依赖：Pillow<10.0.0、easyocr>=1.7.0、numpy>=1.19.0、mcp>=1.0.0、torch>=1.9.0、opencv-python>=4.5.0

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

### 3. MCP服务器模式

#### 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 MCP 服务器
python mcp_server.py

# 3. 测试连接
python test_mcp_client.py
```

#### 启动脚本

**Windows:**
```bash
start_mcp_server.bat
```

**Linux/Mac:**
```bash
chmod +x start_mcp_server.sh
./start_mcp_server.sh
```

#### MCP服务器工具说明

**工具1：replace_image_text**
- **功能**：移除图片中的文字并用新的翻译文字替换
- **参数**：
  - `image_data` (string, 必需): Base64编码的图片数据或图片文件路径
  - `new_text` (string, 必需): 用于替换原图片文字的新文字
  - `font_path` (string, 可选): 自定义字体文件路径（TTF格式），默认None
  - `font_size` (integer, 可选): 新文字的字体大小，默认32
  - `output_format` (string, 可选): 输出格式（'base64' 或 'file'），默认'base64'

**工具2：detect_text_regions**
- **功能**：检测图片中的文字区域（不进行替换）
- **参数**：
  - `image_data` (string, 必需): Base64编码的图片数据或图片文件路径
- **返回**：JSON格式的文字区域信息，包含坐标和尺寸

#### 使用示例

```python
# 示例1：使用文件路径
result = await client.call_tool(
    "replace_image_text",
    {
        "image_data": "test_image.jpg",
        "new_text": "这是替换后的中文文字",
        "font_size": 40,
        "output_format": "base64"
    }
)

# 示例2：使用Base64数据
with open("input.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode('utf-8')

result = await client.call_tool(
    "replace_image_text",
    {
        "image_data": image_b64,
        "new_text": "Replaced English Text",
        "font_path": "arial.ttf",
        "font_size": 36,
        "output_format": "file"
    }
)

# 示例3：检测文字区域
result = await client.call_tool(
    "detect_text_regions",
    {"image_data": "test_image.jpg"}
)

# 输出示例：
# {
#   "detected_regions": 2,
#   "regions": [
#     {"x": 100, "y": 50, "width": 200, "height": 30},
#     {"x": 150, "y": 120, "width": 150, "height": 25}
#   ]
# }
```

#### 集成到不同AI应用

**1. Claude Desktop**

在 Claude Desktop 中配置 MCP 服务器：

1. 打开 Claude Desktop 设置
2. 找到 MCP 配置部分
3. 添加服务器配置：
```json
{
  "command": "python",
  "args": ["/path/to/your/mcp_server.py"],
  "env": {
    "PYTHONPATH": "/path/to/your/project"
  }
}
```

**2. 自定义AI应用**

```python
import asyncio
import mcp.client.stdio
from mcp.client.models import InitializationOptions

async def use_image_text_replacement():
    # 连接到MCP服务器
    async with mcp.client.stdio.stdio_client(
        ["python", "mcp_server.py"]
    ) as (read_stream, write_stream):
        client = mcp.client.stdio.Client(
            read_stream,
            write_stream,
            InitializationOptions(
                client_name="my-app",
                client_version="1.0.0",
                capabilities={},
            ),
        )
        
        # 初始化连接
        await client.initialize()
        
        # 使用工具
        result = await client.call_tool(
            "replace_image_text",
            {
                "image_data": "input.jpg",
                "new_text": "新文字",
                "output_format": "base64"
            }
        )
        
        print(result[0].text)

# 运行
asyncio.run(use_image_text_replacement())
```

#### MCP配置文件

创建 `mcp_config.json` 文件来配置MCP服务器：

```json
{
  "mcpServers": {
    "image-text-replacement": {
      "command": "python",
      "args": ["mcp_server.py"],
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

## 功能流程说明
1. **自动检测图片中的文字区域**（EasyOCR，返回多边形）
2. **对检测到的区域做多边形遮罩+模糊/填充**，最大程度去除原文字
3. **在原位置写入新文字**，支持自适应字号、描边、颜色自定义

## 核心算法参数
- `BOX_EXPAND_SCALE = 1.03`：检测框膨胀比例，越大模糊区域越大，建议1.01~1.10
- `CONFIDENCE_THRESHOLD = 0.4`：OCR置信度阈值，越高越严格
- `MAX_BOXES = 8`：只处理置信度最高的前N个检测框
- `MASK_BLUR_RADIUS = 2`：遮罩羽化半径，越大边缘越柔和
- `FILL_BLUR_RADIUS = 10`：区域背景模糊半径，越大越无痕
- `FINAL_BLUR_RADIUS = 5`：最终整体模糊半径，越大越无痕

## 核心函数说明

### 主要函数
- `remove_text_and_replace()`: 主要功能函数，执行文字检测、去除和替换
- `fast_ocr()`: 快速OCR检测，使用EasyOCR识别文字区域
- `get_adaptive_font()`: 自适应字体大小，确保文字适合检测框
- `expand_box()`: 检测框膨胀，扩大处理区域
- `merge_boxes()`: 合并重叠检测框，避免重复处理

### 辅助函数（当前版本未使用）
- `shrink_polygon()`: 多边形收缩功能（预留）
- `get_region_main_color()`: 区域主色调检测（预留）
- `adaptive_threshold_mask()`: 自适应阈值遮罩（预留）

## 效果说明
- 适合背景较为均匀、文字与背景对比明显的图片
- 对复杂背景、低对比度、雾气/光晕等情况，自动检测和去除效果有限
- 遮罩为多边形，边缘羽化，尽量自然
- 新文字可自定义字体、颜色、描边

## 错误处理

### 常见错误及解决方案

1. **找不到图片文件**
   ```
   错误: 找不到图片文件: input.jpg
   解决: 确保图片文件路径正确，或使用绝对路径
   ```

2. **无效的Base64数据**
   ```
   错误: 无效的 base64 图片数据
   解决: 确保Base64编码正确，支持标准Base64或data URL格式
   ```

3. **字体文件不存在**
   ```
   错误: 字体文件不存在
   解决: 确保字体文件路径正确，或使用系统默认字体
   ```

4. **MCP服务器连接失败**
   ```
   错误: 无法连接到MCP服务器
   解决: 检查Python环境、依赖包安装、文件路径配置
   ```

5. **中文字体显示异常？** 请指定支持中文的.ttf字体（如 simhei.ttf、msyh.ttc）
6. **部分文字未完全去除？** 受限于OCR检测精度和图片复杂度，可尝试更换图片、调整参数或手动辅助
7. **依赖安装失败？** 请确保Python 3.7+，pip已升级，国内可用镜像源加速

## 性能优化建议

1. **图片大小**：建议图片尺寸不超过 2048x2048 像素
2. **字体缓存**：服务器会自动缓存EasyOCR读取器，首次运行较慢
3. **批量处理**：对于多张图片，建议复用MCP连接而不是重复建立
4. **内存使用**：处理大图片时注意内存使用，及时清理临时文件

## 高级配置

### 自定义字体
```python
# 使用自定义字体文件
result = await client.call_tool(
    "replace_image_text",
    {
        "image_data": "input.jpg",
        "new_text": "自定义字体文字",
        "font_path": "/path/to/custom-font.ttf",
        "font_size": 48
    }
)
```

### 输出格式选择
```python
# 获取Base64输出（适合网络传输）
result = await client.call_tool(
    "replace_image_text",
    {
        "image_data": "input.jpg",
        "new_text": "新文字",
        "output_format": "base64"
    }
)

# 保存为文件（适合本地处理）
result = await client.call_tool(
    "replace_image_text",
    {
        "image_data": "input.jpg",
        "new_text": "新文字",
        "output_format": "file"
    }
)
```

## 支持的文件格式

- **输入图片**：JPEG, PNG, BMP, TIFF 等常见格式
- **输出图片**：JPEG 格式
- **字体文件**：TTF, TTC 格式

## 适用场景与局限性
- 适合批量去除/替换图片中的水印、标语、说明等
- 不适合极其复杂背景、艺术字、极低对比度等极端场景
- 若需更高精度，建议结合手动辅助或专业修图工具
- MCP模式特别适合AI应用自动化处理图片文字替换任务

## 注意事项

1. 确保Python环境中有足够的权限读写文件
2. 处理包含敏感信息的图片时注意数据安全
3. 建议在生产环境中使用虚拟环境
4. 定期更新依赖包以获得最新功能和安全性修复
5. EasyOCR首次运行会下载模型文件，需要网络连接

## 文件结构
```
pho/
├── replace_text_in_image.py    # 核心功能模块
├── mcp_server.py              # MCP服务器
├── test_mcp_client.py         # MCP客户端测试
├── mcp_config.json            # MCP配置文件
├── requirements.txt           # 依赖包列表
├── test_image.jpg             # 测试图片
├── start_mcp_server.bat       # Windows启动脚本
├── start_mcp_server.sh        # Linux/Mac启动脚本
└── README.md                  # 说明文档
```

---

如有更多定制需求或遇到特殊问题，欢迎反馈！ 

async def main():
    print("MCP 服务器已启动，等待客户端连接...")
    # ...原有代码... 