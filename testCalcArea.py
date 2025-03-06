import argparse
import json
import os
import ffmpeg

def get_video_info(video_path):
    """使用 ffmpeg.probe 获取视频的宽度和高度"""
    probe = ffmpeg.probe(video_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    width = int(video_stream['width'])
    height = int(video_stream['height'])
    return width, height

def crop_video(video_path, output_path, crop_width, crop_height, x_offset, y_offset):
    """使用 ffmpeg-python 裁剪视频"""
    (
        ffmpeg
        .input(video_path)
        .filter('crop', crop_width, crop_height, x_offset, y_offset)
        .output(output_path, acodec='copy', vcodec='libx264')
        .run()
    )

def generate_output_path(input_path, specified_output=None):
    """生成输出文件路径，确保不覆盖已有文件"""
    if specified_output:
        output_path = specified_output
    else:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}-out{ext}"
    
    while os.path.exists(output_path):
        print(f"Output file {output_path} already exists. Adding '-new' to filename.")
        base, ext = os.path.splitext(output_path)
        output_path = f"{base}-new{ext}"
    
    return output_path

def main():
    parser = argparse.ArgumentParser(description="裁剪视频以适应9:16比例。")
    parser.add_argument("-i", "--input", help="输入视频文件路径")
    parser.add_argument("-o", "--output", help="输出视频文件路径，可选")
    args = parser.parse_args()
    
    video_path = args.input
    output_path = generate_output_path(video_path, args.output)
    target_aspect = 9 / 16
    
    width, height = get_video_info(video_path)
    current_aspect = width / height
    
    if current_aspect > target_aspect:
        # 视频比9:16更宽，裁剪左右
        new_width = int(height * target_aspect)
        x_offset = (width - new_width) // 2
        crop_video(video_path, output_path, new_width, height, x_offset, 0)
    elif current_aspect < target_aspect:
        # 视频比9:16更长，裁剪上下
        new_height = int(width / target_aspect)
        y_offset = (height - new_height) // 2
        crop_video(video_path, output_path, width, new_height, 0, y_offset)
    else:
        print("视频已经是9:16比例，无需裁剪。")

if __name__ == "__main__":
    main()