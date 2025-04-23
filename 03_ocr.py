import os
import argparse
from paddleocr import PaddleOCR
import Levenshtein
import pandas as pd
from translate import Translator

name_mapping = {
    "オズ": "Oz", "アーサー": "Arthur", "カイン": "Cain", "リケ": "Riquet", "スノウ": "Snow",
    "ホワイト": "White", "ミスラ": "Mithra", "オーエン": "Owen", "ブラッドリー": "Bradley",
    "ファウスト": "Faust", "シノ": "Shino", "ヒースクリフ": "Heathcliff", "ネロ": "Nero",
    "シャイロック": "Shylock", "ムル": "Murr", "クロエ": "Chloe", "ラスティカ": "Rustica",
    "フィガロ": "Figaro", "ルチル": "Rutile", "レノックス": "Lennox", "ミチル": "Mitile",

    # Add more mappings as needed
    "晶": "晶",
    "ドラモンド": "Drummond", "ヴィンセント": "Vincent", "ルキーノ": "Luchino",
    "アレク": "Alec",
}

def extract_text_from_image(image_path, ocr, seq):
    def replace_names_in_text(text, mapping):
        for jp_name, en_name in mapping.items():
            text = text.replace(jp_name, en_name)
        return text

    result = ocr.ocr(image_path, cls=True)

    if not result or result == [None]:
        print(f"[LOG] Subtitle {seq}: No text detected")
        return "", ""

    extracted_lines = [word_info[1][0]
                       for line in result for word_info in line]
    if not extracted_lines:
        return "", ""

    potential_speaker = extracted_lines[0]
    if potential_speaker in name_mapping:
        speaker = name_mapping[potential_speaker]
        content = " ".join(extracted_lines[1:]) if len(
            extracted_lines) > 1 else ""
        content = replace_names_in_text(content, name_mapping)
        formatted_text = f"{seq}-{speaker}：{content}"
    else:
        formatted_text = f"{seq}：{' '.join(extracted_lines)}"

    # Perform secondary single-line OCR for additional accuracy
    second_result = ocr.ocr(image_path, cls=False)
    secondary_lines = [word_info[1][0]
                       for line in second_result for word_info in line]

    if secondary_lines:
        combined_text = " ".join(secondary_lines)

        # If secondary OCR extracts more words, merge results using string similarity
        if len(combined_text) > len(" ".join(extracted_lines)):
            if Levenshtein.ratio(combined_text, " ".join(extracted_lines)) < 0.85:
                formatted_text = f"{seq}：{combined_text}"

    print(f"[LOG] Subtitle {seq}: Final Extracted Text -> {formatted_text}")

    return formatted_text, potential_speaker


def process_images_to_csv(slides_path, ocr, translate_to_chn):
    data = []
    for seq in range(1, 10000):  # Assuming a range for seq
        image_filename = f"{seq:04d}.png"
        image_path = os.path.join(slides_path, image_filename)

        if os.path.exists(image_path):
            extracted_text, _ = extract_text_from_image(image_path, ocr, seq)

            # remove seq- prefix
            if "：" in extracted_text:
                _, extracted_text = extracted_text.split("：", 1)

            row = {
                "seq": str(seq),
                "recognized_japanese": extracted_text
            }

            # Translate to Chinese only if enabled
            if translate_to_chn:
                translated_text = translate_japanese_to_chinese(
                    extracted_text)
                row["translated_chinese"] = translated_text

            data.append(row)

    return data


def translate_japanese_to_chinese(japanese_text):
    # print original extracted Japanese text
    print(f"[LOG] Original Extracted Japanese: {japanese_text}")

    # remove seq- prefix
    if "：" in japanese_text:
        _, japanese_text = japanese_text.split("：", 1)

    # pinrt optimized Japanese text for translation input
    print(f"[LOG] Processed Japanese for Translation: {japanese_text}")

    # use translate package to translate Japanese to Chinese
    translator = Translator(from_lang="ja", to_lang="zh")
    translated_text = translator.translate(japanese_text)

    # print translated Chinese text
    print(f"[LOG] Translated Chinese: {translated_text}")
    return translated_text


def main():
    parser = argparse.ArgumentParser(
        description="Process images to extract OCR results and save as CSV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--slides", required=True,
                        help="Path to the slides folder containing PNG images.")
    parser.add_argument("--chn", action="store_true",
                        help="Enable Chinese translation output.")

    args = parser.parse_args()

    ocr = PaddleOCR(
        use_angle_cls=True,  # Keep angle classification for rotated text
        lang='japan',
        drop_score=0.8,  # Filter low-confidence recognition results
        use_dilation=True  # Enhance character edges to improve recognition
    )

    data = process_images_to_csv(args.slides, ocr, args.chn)

    slides_folder_name = os.path.basename(os.path.normpath(args.slides))
    csv_filename = f"{slides_folder_name.replace('-slides', '')}-ocr-results.csv" if '-slides' in slides_folder_name else "-ocr-results.csv"
    csv_path = os.path.join(os.path.dirname(args.slides), csv_filename)
    if os.path.exists(csv_path):
        print(f"[WARNING] File {csv_filename} already exists and will be overwritten.")
    
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)

    print(f"Processed results saved as: {csv_path}")


if __name__ == "__main__":
    main()
