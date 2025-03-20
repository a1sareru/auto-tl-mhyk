import os
import argparse
from paddleocr import PaddleOCR

def load_ass_file(ass_path):
    with open(ass_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return lines

def save_ass_file(ass_path, lines):
    with open(ass_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def extract_text_from_image(image_path, ocr):
    result = ocr.ocr(image_path, det=False, cls=False)
    extracted_text = " ".join([line[0] for res in result for line in res]) if result else ""
    return extracted_text

def process_ass_file(ass_lines, slides_path, ocr):
    processed_lines = []
    for line in ass_lines:
        if line.startswith("Dialogue:"):
            parts = line.strip().split(",")
            text_field = parts[-1]
            seq = text_field.strip()
            image_filename = f"{int(seq):04d}.png"
            image_path = os.path.join(slides_path, image_filename)
            
            if os.path.exists(image_path):
                extracted_text = extract_text_from_image(image_path, ocr)
                parts[-1] = f"{seq}-{extracted_text}"
            
            processed_line = ",".join(parts) + "\n"
            processed_lines.append(processed_line)
        else:
            processed_lines.append(line)
    
    return processed_lines

def main():
    parser = argparse.ArgumentParser(description="Process ASS file by appending OCR results from slides images.")
    parser.add_argument("--slides-path", required=True, help="Path to the slides folder containing PNG images.")
    parser.add_argument("--ass-path", required=True, help="Path to the ASS subtitle file.")

    args = parser.parse_args()

    ocr = PaddleOCR(lang='japan')

    ass_lines = load_ass_file(args.ass_path)
    processed_lines = process_ass_file(ass_lines, args.slides_path, ocr)

    new_ass_path = args.ass_path.replace(".ass", "-ocr.ass")
    save_ass_file(new_ass_path, processed_lines)

    print(f"Processed ASS file saved as: {new_ass_path}")

if __name__ == "__main__":
    main()
