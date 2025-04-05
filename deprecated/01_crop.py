import argparse
import json
import os
import ffmpeg
import re

def get_video_info(video_path):
    """使用 ffmpeg.probe 获取视频的宽度和高度"""
    probe = ffmpeg.probe(video_path)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    width = int(video_stream['width'])
    height = int(video_stream['height'])
    return width, height


def detect_crop_parameters(video_path, target_aspect):
    """使用 ffmpeg 运行 cropdetect 过滤器，仅分析视频的中间1/3，提取出现次数最多的裁剪参数"""
    try:
        # 获取视频时长
        probe = ffmpeg.probe(video_path)
        duration = float(probe['format']['duration'])

        # 计算分析区间
        start_time = duration / 3
        analysis_duration = duration / 3

        # 运行 cropdetect
        result = (
            ffmpeg
            .input(video_path, ss=start_time, t=analysis_duration)  # 选择中间 1/3 时长
            .output('null', vf="cropdetect", format='null', v='info')
            .run(capture_stderr=True)
        )
        stderr_output = result[1].decode('utf-8')

        # 使用正则表达式解析所有的裁剪参数
        crop_params = re.findall(r'crop=(\d+:\d+:\d+:\d+)', stderr_output)

        if crop_params:
            # 统计每个裁剪参数的出现次数
            from collections import Counter
            most_common_crop, count = Counter(crop_params).most_common(1)[0]  # 取出现次数最多的
            print(f"检测到最常见的裁剪参数: {most_common_crop} (出现 {count} 次)")
            width, height, x, y = map(int, most_common_crop.split(':'))
            if x > 0:
                width = width + 2 * x
                x = 0
            # turn weight: height into target aspect ratio
            if width * target_aspect < height:
                height = int(width / target_aspect)
            
            print(f"转换为{target_aspect * 16}:9比例: width={width}, height={height}, x={x}, y={y}")
            return width, height, x, y
        else:
            print("未能检测到裁剪参数")
            return None
    except Exception as e:
        print(f"裁剪参数检测失败: {e}")
        return None


def crop_video_with_detected_params(video_path, output_path, target_aspect):
    """自动检测并裁剪视频"""
    crop_params = detect_crop_parameters(video_path, target_aspect)
    if crop_params:
        width, height, x, y = crop_params
        print(f"采用下述裁剪参数: width={width}, height={height}, x={x}, y={y}")
        crop_video(video_path, output_path, width, height, x, y)
        # print the real ratio of the video
        width, height = get_video_info(output_path)
        print(f"[debug] 裁剪后的视频比例: {width}x{height} [phone mode]")
    else:
        print("未检测到有效的裁剪参数，跳过裁剪")


def crop_video(video_path, output_path, crop_width, crop_height, x_offset, y_offset):
    """使用 ffmpeg-python 裁剪视频，并保留音频"""
    input_video = ffmpeg.input(video_path)  # 读取输入视频
    video = input_video.video.filter('crop', crop_width, crop_height, x_offset, y_offset)  # 裁剪视频
    audio = input_video.audio  # 获取音频流
    out = ffmpeg.output(audio, video, output_path, acodec='copy', vcodec='libx264')  # 输出文件
    out.run()  # 运行 ffmpeg 命令


def generate_output_path(input_path, specified_output=None):
    """生成输出文件路径，确保不覆盖已有文件"""
    if specified_output:
        output_path = specified_output
        # 已经存在该文件，但是是显式指定的路径，此时允许覆盖
        return output_path
    else:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}-out{ext}"
    
    while os.path.exists(output_path):
        print(f"Output file {output_path} already exists. Adding '-new' to filename")
        base, ext = os.path.splitext(output_path)
        output_path = f"{base}-new{ext}"
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description="裁剪视频以适应9:16比例。")
    parser.add_argument("-i", "--input", help="输入视频文件路径")
    parser.add_argument("-o", "--output", help="输出视频文件路径，可选")
    parser.add_argument("--mode", default="9_16", help="目标比例模式，可选: 9_16 或 9_19.5")
    args = parser.parse_args()
    
    TARGET_ASPECT_RATIOS = {
        "9_16": 9 / 16,
        "9_19.5": 9 / 19.5
    }

    if args.mode not in TARGET_ASPECT_RATIOS:
        print(f"不支持的模式: {args.mode}，请选择 '9_16' 或 '9_19.5'")
        return

    target_aspect = TARGET_ASPECT_RATIOS[args.mode]
    
    video_path = args.input
    output_path = generate_output_path(video_path, args.output)
    
    width, height = get_video_info(video_path)
    current_aspect = width / height
    
    print(f"当前目标模式: {args.mode}, 目标比例: {'9:16' if args.mode == '9_16' else '9:19.5'}")
    
    if current_aspect > target_aspect:
        # 视频比目标比例更宽，裁剪左右
        new_width = int(height * target_aspect)
        x_offset = (width - new_width) // 2
        crop_video(video_path, output_path, new_width, height, x_offset, 0)
    elif current_aspect < target_aspect:
        # 视频比目标比例更长，裁剪上下
        crop_video_with_detected_params(video_path, output_path, target_aspect)
              
    else:
        print("视频已经是目标比例，无需裁剪。")


if __name__ == "__main__":
    main()