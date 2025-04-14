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

def create_pdf(images, output_pdf, size=4):
    """ 将原始图片分组拼接并合并为 PDF，每页 size 张图片，页面尺寸恰好匹配 """
    if not images:
        return

    img_sample = Image.open(images[0])
    img_width, img_height = img_sample.size

    pdf = FPDF(unit="pt", format=(img_width, img_height * size))
    pdf.set_auto_page_break(auto=False)

    for i in range(0, len(images), size):
        group = images[i:i+size]
        pdf.add_page()

        for j, img_path in enumerate(group):
            pdf.image(img_path, 0, j * img_height, img_width, img_height)

    pdf.output(output_pdf, "F")

def main():
    parser = argparse.ArgumentParser(description="图片合成长图并可选生成 PDF")
    parser.add_argument("--slides", required=True, help="输入的图片文件夹路径")
    parser.add_argument("--size", type=int, default=4, help="每组合并的图片数量，默认为 4")
    parser.add_argument("--pdf", action="store_true", help="是否生成 PDF 文件")
    
    args = parser.parse_args()
    
    slides_path = args.slides
    slides_long_path = slides_path + "-long"
    
    images = load_images(slides_path)
    if not images:
        print("未找到任何图片文件")
        return
    
    long_images = create_long_images(images, slides_long_path, args.size)

    if args.pdf:
        output_pdf_name = os.path.basename(slides_path) + "-long.pdf"
        output_pdf = os.path.join(slides_path, output_pdf_name)
        create_pdf(images, output_pdf, args.size)
        print(f"PDF 生成完成: {output_pdf}")

if __name__ == "__main__":
    main()