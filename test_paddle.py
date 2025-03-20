import sys
from paddleocr import PaddleOCR

def recognize_text(image_path):
    # 初始化 OCR，指定语言为日语（japan）
    ocr = PaddleOCR(use_angle_cls=True, lang="japan")
    
    # 进行 OCR 识别
    result = ocr.ocr(image_path, cls=True)
    
    # 输出识别结果
    if result is None:
        print("未能识别出任何文本。")
        return
    
    print("识别结果：")
    for line in result:
        for word_info in line:
            text = word_info[1][0]  # 获取识别的文本
            confidence = word_info[1][1]  # 置信度
            print(f"文本: {text} | 置信度: {confidence:.2f}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("用法: python script.py <图片路径>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    recognize_text(image_path)