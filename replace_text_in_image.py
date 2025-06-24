import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageChops
import easyocr
import time

# ====== 可调参数区 ======
BOX_EXPAND_SCALE = 1.03  # 检测框膨胀比例，越大模糊区域越大，建议1.01~1.10
CONFIDENCE_THRESHOLD = 0.4  # OCR置信度阈值，越高越严格
MAX_BOXES = 8  # 只处理置信度最高的前N个检测框
MASK_BLUR_RADIUS = 2  # 遮罩羽化半径，越大边缘越柔和
FILL_BLUR_RADIUS = 10  # 区域背景模糊半径，越大越无痕
FINAL_BLUR_RADIUS = 5  # 最终整体模糊半径，越大越无痕
# =======================

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
    min_height = int(target_height * 0.8)
    max_width = int(target_width * 1.1)
    font_size = target_height
    if font_path:
        while font_size > 0:
            font = ImageFont.truetype(font_path, font_size)
            bbox = font.getbbox(text)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if h >= min_height and h <= target_height and w <= max_width:
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


def expand_box(x, y, w, h, scale, img_w, img_h):
    # 检测框膨胀，scale为比例
    cx = x + w / 2
    cy = y + h / 2
    new_w = w * scale
    new_h = h * scale
    new_x = int(max(cx - new_w / 2, 0))
    new_y = int(max(cy - new_h / 2, 0))
    new_w = int(min(new_w, img_w - new_x))
    new_h = int(min(new_h, img_h - new_y))
    return new_x, new_y, new_w, new_h


def merge_boxes(boxes, iou_threshold=0.2):
    # 合并重叠检测框
    def iou(box1, box2):
        x1, y1, w1, h1 = box1
        x2, y2, w2, h2 = box2
        xi1 = max(x1, x2)
        yi1 = max(y1, y2)
        xi2 = min(x1 + w1, x2 + w2)
        yi2 = min(y1 + h1, y2 + h2)
        inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        box1_area = w1 * h1
        box2_area = w2 * h2
        union_area = box1_area + box2_area - inter_area
        return inter_area / union_area if union_area > 0 else 0
    merged = []
    for box in boxes:
        found = False
        for i, m in enumerate(merged):
            if iou(box, m) > iou_threshold:
                x1 = min(box[0], m[0])
                y1 = min(box[1], m[1])
                x2 = max(box[0] + box[2], m[0] + m[2])
                y2 = max(box[1] + box[3], m[1] + m[3])
                merged[i] = (x1, y1, x2 - x1, y2 - y1)
                found = True
                break
        if not found:
            merged.append(box)
    return merged


def fast_ocr(image, reader, max_boxes=MAX_BOXES):
    enhancer = ImageEnhance.Contrast(image)
    img_c = enhancer.enhance(1.5)
    result = reader.readtext(np.array(img_c))
    img_w, img_h = image.size
    # 只保留置信度最高的前max_boxes个检测框
    result = sorted(result, key=lambda x: float(x[2]) if x[2] else 0, reverse=True)[:max_boxes]
    boxes = []
    for (bbox, text, conf) in result:
        try:
            conf_val = float(conf)
        except Exception:
            conf_val = 1.0
        if conf_val > CONFIDENCE_THRESHOLD:
            x_coords = [int(point[0]) for point in bbox]
            y_coords = [int(point[1]) for point in bbox]
            x, y, w, h = min(x_coords), min(y_coords), max(x_coords)-min(x_coords), max(y_coords)-min(y_coords)
            x, y, w, h = expand_box(x, y, w, h, BOX_EXPAND_SCALE, img_w, img_h)
            boxes.append((x, y, w, h))
    return merge_boxes(boxes)


def remove_text_and_replace(image_path, new_text, output_path, font_path=None, font_size=32, reader=None):
    start_time = time.time()
    try:
        image = Image.open(image_path)
    except Exception as e:
        raise FileNotFoundError(f"Image not found or cannot be opened: {image_path} - {e}")
    if image.mode != 'RGB':
        image = image.convert('RGB')

    if reader is None:
        reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    rects = fast_ocr(image, reader)
    if not rects:
        print("No text detected in image")
        print(f"Total time used: {time.time() - start_time:.2f} seconds")
        return

    # 遮罩羽化半径可调
    mask = Image.new('L', image.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    for (x, y, w, h) in rects:
        draw_mask.rectangle([x, y, x + w, y + h], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=MASK_BLUR_RADIUS))

    # 区域背景模糊半径可调
    fill_img = image.copy()
    for (x, y, w, h) in rects:
        region_bg = image.crop((x, y, x + w, y + h)).filter(ImageFilter.GaussianBlur(radius=FILL_BLUR_RADIUS))
        fill_img.paste(region_bg, (x, y))
    blurred = fill_img.filter(ImageFilter.GaussianBlur(radius=FINAL_BLUR_RADIUS))
    result_img = fill_img.copy()
    result_img.paste(blurred, mask=mask)

    draw = ImageDraw.Draw(result_img)
    for (x, y, w, h) in rects:
        font = get_adaptive_font(font_path, new_text, h, w)
        try:
            bbox = draw.textbbox((0, 0), new_text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
        except AttributeError:
            text_w, text_h = draw.textsize(new_text, font=font)
        text_x = x + (w - text_w) // 2
        text_y = y + (h - text_h) // 2
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    draw.text((text_x + dx, text_y + dy), new_text, fill=(0,0,0), font=font)
        draw.text((text_x, text_y), new_text, fill=(255,255,255), font=font)

    result_img.save(output_path)
    print(f"Successfully saved: {output_path}")
    print(f"Replaced text in {len(rects)} regions")
    print(f"Total time used: {time.time() - start_time:.2f} seconds")


def main():
    parser = argparse.ArgumentParser(description="Remove text from image and replace with new text.")
    parser.add_argument('--image', required=True, help='Path to input image')
    parser.add_argument('--text', required=True, help='Text to write into image')
    parser.add_argument('--output', required=True, help='Path to save output image')
    parser.add_argument('--font', default=None, help='Path to .ttf font file (optional)')
    parser.add_argument('--fontsize', type=int, default=32, help='Font size (default: 32)')
    args = parser.parse_args()
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    remove_text_and_replace(args.image, args.text, args.output, args.font, args.fontsize, reader=reader)

if __name__ == '__main__':
    main()