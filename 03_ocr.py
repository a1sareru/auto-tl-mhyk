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

def extract_text_from_image(image_path, ocr, seq):
    name_mapping = {
        "オズ": "Oz", "アーサー": "Arthur", "カイン": "Cain", "リケ": "Riquet", "スノウ": "Snow",
        "ホワイト": "White", "ミスラ": "Mithra", "オーエン": "Owen", "ブラッドリー": "Bradley",
        "ファウスト": "Faust", "シノ": "Shino", "ヒースクリフ": "Heathcliff", "ネロ": "Nero",
        "シャイロック": "Shylock", "ムル": "Murr", "クロエ": "Chloe", "ラスティカ": "Rustica",
        "フィガロ": "Figaro", "ルチル": "Rutile", "レノックス": "Lennox", "ミチル": "Mitile"
    }
    
    def replace_names_in_text(text, mapping):
        for jp_name, en_name in mapping.items():
            text = text.replace(jp_name, en_name)
        return text

    result = ocr.ocr(image_path, cls=True)
    
    if not result:
        print(f"[LOG] Subtitle {seq}: No text detected")
        return f"{seq}-未知："

    extracted_lines = [word_info[1][0] for line in result for word_info in line]

    if not extracted_lines:
        return f"{seq}-未知："

    speaker = extracted_lines[0]
    speaker = name_mapping.get(speaker, speaker)
    content = "" if len(extracted_lines) == 1 else " ".join(extracted_lines[1:])
    content = replace_names_in_text(content, name_mapping)

    formatted_text = f"{seq}-{speaker}：{content}"
    
    print(f"[LOG] Subtitle {seq}: Extracted Text -> {formatted_text}")
    
    return formatted_text

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
                extracted_text = extract_text_from_image(image_path, ocr, seq)
                parts[-1] = extracted_text
            
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

    ocr = PaddleOCR(
        use_angle_cls=True,  # Keep angle classification for rotated text
        lang='japan', 
        drop_score=0.8,  # Filter low-confidence recognition results
        use_dilation=True  # Enhance character edges to improve recognition
    )

    ass_lines = load_ass_file(args.ass_path)
    processed_lines = process_ass_file(ass_lines, args.slides_path, ocr)

    new_ass_path = args.ass_path.replace(".ass", "-ocr.ass")
    save_ass_file(new_ass_path, processed_lines)

    print(f"Processed ASS file saved as: {new_ass_path}")

if __name__ == "__main__":
    main()
