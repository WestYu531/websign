from PIL import Image
import random
import os
import json

def paste_signs_on_background(background_image_path, main_folder, output_folder, sign_count, background_color, num_images):
    """
    生成多张图片，并为每张图片生成一个对应的 JSON 文件。

    参数:
    background_image_path (str): 背景图片路径
    main_folder (str): 主文件夹路径，包含标志的类别文件夹
    output_folder (str): 输出图片和 JSON 文件的目标文件夹
    sign_count (int): 每张图片粘贴的标志数量
    background_color (str): 去除的背景颜色 ('white', 'black', 'none')
    num_images (int): 生成图片的数量
    """
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)  # 创建输出文件夹（如果不存在）

        for img_num in range(1, num_images + 1):
            # 打开背景图
            background = Image.open(background_image_path)
            bg_width, bg_height = background.size

            # 获取主文件夹中所有子类别文件夹的标志图片文件路径
            all_signs = []
            for root, dirs, files in os.walk(main_folder):
                for file in files:
                    if file.endswith(('png', 'jpg', 'jpeg')):
                        all_signs.append(os.path.join(root, file))

            # 如果 sign_count 大于现有标志的数量，使用现有数量
            sign_count = min(sign_count, len(all_signs))

            # 随机选择 sign_count 个标志
            selected_signs = random.sample(all_signs, sign_count)  # 随机选择

            pasted_signs = []  # 保存标志的区域
            json_data = []

            for sign_file in selected_signs:
                # 获取标志的类别（文件夹名称作为类别）
                category = os.path.basename(os.path.dirname(sign_file))

                # 根据用户选择去除背景颜色
                if background_color != "none":
                    sign_image = remove_background(sign_file, background_color)
                else:
                    sign_image = Image.open(sign_file).convert("RGBA")  # 不去除背景，直接加载图片

                # 随机调整标志大小
                sign_image, sign_size = resize_sign(sign_image)

                sign_width, sign_height = sign_image.size

                # 寻找可用区域
                max_attempts = 100  
                for _ in range(max_attempts):
                    # 随机选择区域
                    random_x = random.randint(0, bg_width - sign_width)
                    random_y = random.randint(0, bg_height - sign_height)
                    new_sign_area = (random_x, random_y, random_x + sign_width, random_y + sign_height)

                    # 检查重叠
                    if not check_overlap(new_sign_area, pasted_signs):
                        background.paste(sign_image, (random_x, random_y), sign_image)
                        pasted_signs.append(new_sign_area)

                        # 获取标志名称
                        sign_name = os.path.basename(sign_file)

                        # 添加标志信息到 json_data，包括 category
                        json_data.append({
                            "sign_name": sign_name,
                            "category": category,  # 添加类别信息
                            "top_left": [random_x, random_y],
                            "bottom_right": [random_x + sign_width, random_y + sign_height],
                            "size": f"{sign_size}*{sign_size}"
                        })
                        break

            # 构建输出文件名
            output_image_path = os.path.join(output_folder, f"output_image_{img_num}.png")
            json_output_path = os.path.join(output_folder, f"output_image_{img_num}.json")

            # 保存图片
            if output_image_path.endswith(".jpg"):
                background = background.convert("RGB")
            background.save(output_image_path)
            print(f"图片已保存为 {output_image_path}")

            # 保存 JSON 文件
            with open(json_output_path, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)

            print(f"JSON 文件已保存为 {json_output_path}")

    except Exception as e:
        print(f"出现错误: {e}")

def remove_background(sign_file_path, background_color):
    """
    去除图片中的指定背景颜色，替换为透明背景。

    参数:
    sign_file_path (str): 标志图片文件路径
    background_color (str): 要去除的背景颜色，'white' 或 'black'

    返回:
    PIL.Image: 去除背景后的标志图片
    """
    # 打开图片
    img = Image.open(sign_file_path).convert("RGBA")

    # 获取图片的数据
    datas = img.getdata()

    new_data = []
    
    # 根据用户选择去除背景颜色
    for item in datas:
        if background_color == "white" and item[0] > 200 and item[1] > 200 and item[2] > 200:
            new_data.append((255, 255, 255, 0))  # 白色设为透明
        elif background_color == "black" and item[0] < 50 and item[1] < 50 and item[2] < 50:
            new_data.append((0, 0, 0, 0))  # 黑色设为透明
        else:
            new_data.append(item)

    # 将处理后的像素数据赋值给图片
    img.putdata(new_data)

    return img

def resize_sign(sign_image):
    """
    随机调整标志（小图片）的大小，范围为 42x42 到 300x300，保持长宽比例。

    参数:
    sign_image (PIL.Image): 输入的标志图片

    返回:
    PIL.Image: 调整大小后的标志图片，保持长宽比例
    tuple: 返回 sign 的大小
    """
    original_width, original_height = sign_image.size

    # 随机选择大小
    max_size = random.randint(42, 300)

    # 按比例调整尺寸
    if original_width > original_height:
        new_width = max_size
        new_height = int((max_size / original_width) * original_height)
    else:
        new_height = max_size
        new_width = int((max_size / original_height) * original_width)

    resized_sign = sign_image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return resized_sign, max_size

def check_overlap(new_area, existing_areas):
    """
    检查新标志区域是否与已有的标志区域重叠。

    参数:
    new_area (tuple): 新标志的区域 (x1, y1, x2, y2)
    existing_areas (list): 已有标志的区域列表，每个区域为 (x1, y1, x2, y2)

    返回:
    bool: 如果重叠返回 True，否则返回 False
    """
    for area in existing_areas:
        if not (new_area[2] <= area[0] or new_area[0] >= area[2] or new_area[3] <= area[1] or new_area[1] >= area[3]):
            return True  # 存在重叠
    return False  # 没有重叠

# 获取用户输入
background_color = input("你想要去除的背景颜色是什么？输入 'white'（白色） 或 'black'（黑色） 或 'none'（不去除背景）: ").strip().lower()

# 示例调用
background_image_path = '/Users/westyu/Desktop/2.png'  # 背景图片路径
main_folder = '/Users/westyu/Desktop/archive'  # 主文件夹路径，包含标志的类别文件夹
output_folder = '/Users/westyu/Desktop/2'  # 输出图片和 JSON 文件的目标文件夹
sign_count = 15  # 每张图片的标志数量
num_images = 10  # 生成图片的数量

paste_signs_on_background(background_image_path, main_folder, output_folder, sign_count, background_color, num_images)