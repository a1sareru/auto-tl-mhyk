import os
import subprocess
import argparse

parser = argparse.ArgumentParser(description="使用 ffmpeg 裁剪视频")
parser.add_argument("--input", required=True, help="输入目录，包含 mp4 文件")
parser.add_argument("--output", required=True, help="输出目录，保存裁剪后的视频")
args = parser.parse_args()

input_dir = args.input
output_dir = args.output

# 创建输出目录（如果不存在）
os.makedirs(output_dir, exist_ok=True)

# 遍历文件夹
for filename in os.listdir(input_dir):
    if filename.endswith(".mp4"):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        # ffmpeg 裁剪命令
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-vf", "crop=1080:1920:0:284",
            # "-vf", "crop=1080:2340:0:30",
            "-y",  # 自动覆盖
            output_path
        ]

        print(f"Processing {filename}...")
        subprocess.run(cmd)

print("所有视频处理完成。")
