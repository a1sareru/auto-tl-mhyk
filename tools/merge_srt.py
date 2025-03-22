import os
import re
import sys
import yaml
import argparse
from datetime import timedelta
from fractions import Fraction
from moviepy.editor import VideoFileClip
import ffmpeg
import tempfile
from shutil import move
from collections import Counter

def parse_srt_time(s):
    h, m, rest = s.split(":")
    s, ms = rest.split(",")
    return timedelta(hours=int(h), minutes=int(m), seconds=int(s), milliseconds=int(ms))

def format_srt_time(t):
    total_seconds = int(t.total_seconds())
    ms = t.microseconds // 1000
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def shift_srt(srt_path, offset: timedelta):
    new_lines = []
    with open(srt_path, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})", line)
            if match:
                start = parse_srt_time(match.group(1)) + offset
                end = parse_srt_time(match.group(2)) + offset
                new_lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}\n")
            else:
                new_lines.append(line)
    return new_lines

def get_video_duration(path):
    clip = VideoFileClip(path)
    return clip.duration  # in seconds

def load_paths_from_yaml(yaml_path, base_prefix=''):
    if not os.path.exists(yaml_path):
        print(f"❌ YAML 文件未找到: {yaml_path}")
        sys.exit(1)

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    video_paths = []
    srt_paths = []

    for item in data:
        if "video_paths" in item:
            video_paths = item["video_paths"]
        elif "srt_paths" in item:
            srt_paths = item["srt_paths"]

    if not video_paths or not srt_paths:
        print("❌ YAML 文件格式错误，必须包含 video_paths 和 srt_paths")
        sys.exit(1)

    if len(video_paths) != len(srt_paths):
        print("❌ 视频数量与字幕数量不一致，请检查 YAML 配置")
        sys.exit(1)

    base_dir = os.path.abspath(base_prefix) if base_prefix else os.path.dirname(yaml_path)
    video_paths = [os.path.join(base_dir, path) for path in video_paths]
    srt_paths = [os.path.join(base_dir, path) for path in srt_paths]

    for path in video_paths + srt_paths:
        if not os.path.exists(path):
            print(f"❌ 找不到文件: {path}")
            print("   请确保路径是正确的相对路径或绝对路径")
            sys.exit(1)

    return video_paths, srt_paths

def merge_srt_and_shift(video_paths, srt_paths, output_path):
    offset = timedelta(seconds=0)
    all_lines = []
    index = 1

    for video, srt in zip(video_paths, srt_paths):
        duration = get_video_duration(video)
        shifted_lines = shift_srt(srt, offset)

        block = []
        for line in shifted_lines:
            clean_line = line.replace('\ufeff', '')
            if re.match(r"^\s*\d+\s*$", clean_line):
                continue
            if clean_line.strip() == "":
                if block:
                    all_lines.append(f"{index}\n")
                    all_lines.extend(block)
                    all_lines.append("\n")
                    index += 1
                    block = []
            else:
                block.append(clean_line)
        if block:
            all_lines.append(f"{index}\n")
            all_lines.extend(block)
            all_lines.append("\n")

        offset += timedelta(seconds=duration)

    # Re-assign subtitle indices to ensure they are sequential
    numbered_lines = []
    new_index = 1
    i = 0
    while i < len(all_lines):
        if re.match(r"^\d+\n?$", all_lines[i].strip()):
            numbered_lines.append(f"{new_index}\n")
            new_index += 1
            i += 1
        else:
            numbered_lines.append(all_lines[i])
            i += 1
    all_lines = numbered_lines

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(all_lines)

    print(f"✅ 合并完成：{os.path.abspath(output_path)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--yml-relative-base', '-yrb', type=str, default='', help='指定用于解析 YAML 中路径的基准目录')
    args = parser.parse_args()
    base_prefix = args.yml_relative_base

    script_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_path = os.path.join(script_dir, "merge_srt.yml")

    video_files, srt_files = load_paths_from_yaml(yaml_path, base_prefix)

    if base_prefix:
        base_abs = os.path.abspath(base_prefix)
        srt_output_path = os.path.join(base_abs, "merged.srt")
        video_output_path = os.path.join(base_abs, "merged.mp4")
    else:
        srt_output_path = os.path.join(os.getcwd(), "merged.srt")
        video_output_path = os.path.join(os.getcwd(), "merged.mp4")

    merge_srt_and_shift(video_files, srt_files, srt_output_path)

    print("🎬 视频信息摘要：")
    for path in video_files:
        try:
            probe = ffmpeg.probe(path)
            vstream = next((s for s in probe["streams"] if s["codec_type"] == "video"), None)
            astream = next((s for s in probe["streams"] if s["codec_type"] == "audio"), None)
            if vstream:
                print(f"  - {os.path.basename(path)}: video codec={vstream.get('codec_name')}, resolution={vstream.get('width')}x{vstream.get('height')}, framerate={vstream.get('r_frame_rate')}")
            if astream:
                print(f"    audio codec={astream.get('codec_name')}, sample_rate={astream.get('sample_rate')}, channels={astream.get('channels')}")
        except Exception as e:
            print(f"⚠️ 无法获取 {os.path.basename(path)} 的信息: {e}")