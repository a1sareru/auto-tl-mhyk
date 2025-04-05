import os
import argparse
from pathlib import Path
import pysubs2

def convert_ass_to_srt(input_path: Path, output_path: Path):
    subs = pysubs2.load(str(input_path), encoding="utf-8")
    output_file = output_path / (input_path.stem + ".srt")
    subs.save(str(output_file), format="srt")
    print(f"Converted: {input_path.name} -> {output_file.name}")

def main():
    parser = argparse.ArgumentParser(description="批量将ASS字幕转为SRT格式")
    parser.add_argument("input", help="输入目录，包含ass字幕")
    
    args = parser.parse_args()
    input_dir = Path(args.input)
    output_dir = input_dir / "srt"

    if not input_dir.exists() or not input_dir.is_dir():
        print("输入目录不存在或不是目录")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    for file in input_dir.glob("*.ass"):
        try:
            convert_ass_to_srt(file, output_dir)
        except Exception as e:
            print(f"转换失败：{file.name}，错误：{e}")

if __name__ == "__main__":
    main()