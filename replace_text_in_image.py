import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import easyocr


def shrink_polygon(polygon, shrink_pixels=8):
    # 多边形向中心收缩
    cx = sum([p[0] for p in polygon]) / len(polygon)
    cy = sum([p[1] for p in polygon]) / len(polygon)
    new_poly = []
    for x, y in polygon:
        vec_x = x - cx
        vec_y = y - cy
        length = (vec_x ** 2 + vec_y ** 2) ** 0.5
        if length == 0:
            new_poly.append((x, y))
        else:
            ratio = max((length - shrink_pixels) / length, 0)
            new_x = cx + vec_x * ratio
            new_y = cy + vec_y * ratio
            new_poly.append((int(new_x), int(new_y)))
    return new_poly


def get_adaptive_font(font_path, text, target_height, target_width):
    # 动态调整字体大小，使文字高度和宽度都接近目标区域
    font_size = target_height
    if font_path:
        while font_size > 0:
            font = ImageFont.truetype(font_path, font_size)
            bbox = font.getbbox(text)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if h <= target_height and w <= target_width:
                return font
            font_size -= 1
        return ImageFont.truetype(font_path, 1)
    else:
        return ImageFont.load_default()


def get_region_main_color(image, x, y, w, h):
    region = image.crop((x, y, x + w, y + h))
    arr = np.array(region).reshape(-1, 3)
    if len(arr) == 0:
        return (0, 0, 0)
    color = tuple(np.mean(arr, axis=0).astype(int))
    return color


def adaptive_threshold_mask(region):
    # region: PIL Image, RGB
    gray = region.convert('L')
    arr = np.array(gray)
    # 自适应阈值
    mean = np.mean(arr)
    mask = (arr < mean - 5).astype(np.uint8) * 255  # 阈值更宽松
    return Image.fromarray(mask, mode='L')


def remove_text_and_replace(image_path, new_text, output_path, font_path=None, font_size=32):
    try:
        image = Image.open(image_path)
    except Exception as e:
        raise FileNotFoundError(f"Image not found or cannot be opened: {image_path} - {e}")
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # 1. 图像预处理：增强对比度
    enhancer = ImageEnhance.Contrast(image)
    image_enhanced = enhancer.enhance(1.5)

    # 2. EasyOCR检测文字区域
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    result = reader.readtext(np.array(image_enhanced))
    
    polygons = []
    rects = []
    # 3. 过滤低可信度结果
    for (bbox, text, conf) in result:
        try:
            conf_val = float(conf)
        except Exception:
            conf_val = 1.0
        if conf_val > 0.4:
            poly = [(int(x), int(y)) for x, y in bbox]
            poly = shrink_polygon(poly, shrink_pixels=8)
            polygons.append(poly)
            x_coords = [p[0] for p in poly]
            y_coords = [p[1] for p in poly]
            x, y, w, h = min(x_coords), min(y_coords), max(x_coords)-min(x_coords), max(y_coords)-min(y_coords)
            rects.append((x, y, w, h))
    if not polygons:
        print("No text detected in image")
        return

    # 4. 构建像素级mask
    mask = Image.new('L', image.size, 0)
    fill_img = image.copy()
    for poly, (x, y, w, h) in zip(polygons, rects):
        region = image.crop((x, y, x + w, y + h))
        region_mask = adaptive_threshold_mask(region)
        region_mask_full = Image.new('L', image.size, 0)
        region_mask_full.paste(region_mask, (x, y))
        poly_mask = Image.new('L', image.size, 0)
        ImageDraw.Draw(poly_mask).polygon(poly, fill=255)
        region_mask_full = Image.composite(region_mask_full, Image.new('L', image.size, 0), poly_mask)
        mask = ImageChops.lighter(mask, region_mask_full)
        # 先用背景色填充mask区域
        region_bg = image.crop((x, y, x + w, y + h)).filter(ImageFilter.GaussianBlur(radius=15))
        fill_img.paste(region_bg, (x, y), region_mask)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=2))

    # 5. 只对mask区域做局部模糊
    blurred = fill_img.filter(ImageFilter.GaussianBlur(radius=8))
    result_img = fill_img.copy()
    result_img.paste(blurred, mask=mask)

    # 6. 写入新文字
    draw = ImageDraw.Draw(result_img)
    for (poly, (x, y, w, h)) in zip(polygons, rects):
        font = get_adaptive_font(font_path, new_text, h, w)
        try:
            bbox = draw.textbbox((0, 0), new_text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = draw.textsize(new_text, font=font)
        text_x = x + (w - text_w) // 2
        text_y = y + (h - text_h) // 2
        # 黑色描边
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    draw.text((text_x + dx, text_y + dy), new_text, fill=(0,0,0), font=font)
        # 白色文字
        draw.text((text_x, text_y), new_text, fill=(255,255,255), font=font)

    result_img.save(output_path)
    print(f"Successfully saved: {output_path}")
    print(f"Replaced text in {len(polygons)} regions")


def main():
    parser = argparse.ArgumentParser(description="Remove text from image and replace with new text.")
    parser.add_argument('--image', required=True, help='Path to input image')
    parser.add_argument('--text', required=True, help='Text to write into image')
    parser.add_argument('--output', required=True, help='Path to save output image')
    parser.add_argument('--font', default=None, help='Path to .ttf font file (optional)')
    parser.add_argument('--fontsize', type=int, default=32, help='Font size (default: 32)')
    args = parser.parse_args()
    remove_text_and_replace(args.image, args.text, args.output, args.font, args.fontsize)

if __name__ == '__main__':
    main()