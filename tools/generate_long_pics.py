import os
import argparse
from PIL import Image
from fpdf import FPDF

def pad_number(number, length=4):
    """ 将数字转换为指定长度的字符串，前导补0 """
    return str(number).zfill(length)

def load_images(slides_path):
    """ 读取并按编号排序所有图片 """
    images = []
    for filename in sorted(os.listdir(slides_path)):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            images.append(os.path.join(slides_path, filename))
    return images

def create_long_images(images, slides_long_path, size=4):
    """ 按 size 组装图片为长图 """
    os.makedirs(slides_long_path, exist_ok=True)
    long_images = []

    for i in range(0, len(images), size):
        group = images[i:i+size]
        img_list = [Image.open(img) for img in group]
        
        # 计算新图片的宽高
        width, height = img_list[0].size
        total_height = sum(img.size[1] for img in img_list)
        long_image = Image.new("RGB", (width, total_height))

        # 拼接图片
        y_offset = 0
        for img in img_list:
            long_image.paste(img, (0, y_offset))
            y_offset += img.size[1]
        
        # 生成输出文件名
        out_filename = os.path.join(slides_long_path, f"long_{pad_number(i // size)}.png")
        long_image.save(out_filename)
        long_images.append(out_filename)

    return long_images

def create_pdf(long_images, output_pdf):
    """ 将生成的长图合并为 PDF，并确保页面尺寸匹配图片实际尺寸 """
    pdf = FPDF(unit="pt")  # 设定单位为点 (pt)，避免单位转换误差

    for img_path in long_images:
        img = Image.open(img_path)
        width, height = img.size

        # 设置自定义页面大小
        pdf.add_page()
        pdf.set_auto_page_break(auto=False)  # 禁止自动分页
        pdf.image(img_path, 0, 0, width, height)

    pdf.output(output_pdf, "F")

def main():
    parser = argparse.ArgumentParser(description="图片合成长图并可选生成 PDF")
    parser.add_argument("--slides", required=True, help="输入的图片文件夹路径")
    parser.add_argument("--size", type=int, default=4, help="每组合并的图片数量，默认为 4")
    parser.add_argument("--pdf", action="store_true", help="是否生成 PDF 文件")
    
    args = parser.parse_args()
    
    slides_path = args.slides
    slides_long_path = os.path.join(os.path.dirname(slides_path), "slides-long")
    
    images = load_images(slides_path)
    if not images:
        print("未找到任何图片文件")
        return
    
    long_images = create_long_images(images, slides_long_path, args.size)

    if args.pdf:
        output_pdf = os.path.join(os.path.dirname(slides_path), "slides-long.pdf")
        create_pdf(long_images, output_pdf)
        print(f"PDF 生成完成: {output_pdf}")

if __name__ == "__main__":
    main()