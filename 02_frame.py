import argparse
import os
import shutil
import cv2
import numpy as np
import csv
import ffmpeg
import re
import yaml

# === User's Configuration ===
# Path to the reference image (can be modified as needed)
# 参考图像路径（可按需修改）
KUROYURI_PATH = "kuroyuri.png"

# Similarity threshold ratio for detecting frame peaks (default: 0.97)
# 相似度阈值，用于识别高峰帧区间（默认值：0.97）
THRESHOLD_RATIO = 0.97

# Configuration Presets

CONFIG_PRESETS = {
    "9_16": {
        "DEFAULT_WIDTH": 1080,
        "DEFAULT_HEIGHT": 1920,
        "YURI_X1_RATIO": 0.872,
        "YURI_Y1_RATIO": 0.809,
        "YURI_X2_RATIO": 0.94,
        "YURI_Y2_RATIO": 0.85,
        "SLIDE_X1_RATIO": 0.074,
        "SLIDE_Y1_RATIO": 0.672,
        "SLIDE_X2_RATIO": 0.888,
        "SLIDE_Y2_RATIO": 0.839
    },
    "9_19.5": {
        # Preset for aspect ratio 9:19.5
        "DEFAULT_WIDTH": 1080,
        "DEFAULT_HEIGHT": 2340,
        "YURI_X1_RATIO": 0.872,
        "YURI_Y1_RATIO": 0.757,
        "YURI_X2_RATIO": 0.945,
        "YURI_Y2_RATIO": 0.794,
        "SLIDE_X1_RATIO": 0.082,
        "SLIDE_Y1_RATIO": 0.641,
        "SLIDE_X2_RATIO": 0.884,
        "SLIDE_Y2_RATIO": 0.773
    }
}


def parse_args():
    parser = argparse.ArgumentParser(description="Extract frames from video, apply sharpening, binarization, compute similarity with reference image, and generate subtitles.")
    parser.add_argument("--input", type=str, required=True, help="Path to the input video file.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode to save tmp_frame images.")
    parser.add_argument("--slides", action="store_true", help="Enable slides generation for high similarity intervals.")
    return parser.parse_args()

def is_valid_aspect_ratio(width, height):
    if abs((width / height) - (9 / 16)) < 0.05:
        print("Aspect ratio mode: 9:16")
        return "9_16"
    if abs((width / height) - (1080 / 2340)) < 0.01:
        print("Aspect ratio mode: 9:19.5")
        return "9_19.5"
    return None

def enhance_sharpness(image):
    kernel = np.array([[-1, -1, -1],
                       [-1, 9, -1],
                       [-1, -1, -1]])
    return cv2.filter2D(image, -1, kernel)

def binarize_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def compute_similarity(image1, image2):
    image2_resized = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
    diff = cv2.absdiff(image1, image2_resized)
    similarity = 1 - (np.sum(diff) / (255 * image1.shape[0] * image1.shape[1]))
    return similarity

def get_video_resolution(video_path):
    try:
        probe = ffmpeg.probe(video_path)
        video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
        if video_streams:
            width = int(video_streams[0]['width'])
            height = int(video_streams[0]['height'])
            return width, height
    except ffmpeg.Error as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
    return None, None

def extract_frames(video_path, debug, slides):
    # Configuration loading removed; using manual constants
    # Validate THRESHOLD_RATIO
    if not isinstance(THRESHOLD_RATIO, (float, int)) or THRESHOLD_RATIO <= 0 or THRESHOLD_RATIO > 1:
        print(f"Error: Invalid THRESHOLD_RATIO value: {THRESHOLD_RATIO}. It must be a number between 0 and 1.")
        return
    if THRESHOLD_RATIO < 0.8:
        print(f"Warning: THRESHOLD_RATIO={THRESHOLD_RATIO} is very low and may lead to false detections.")

    video_dir, video_filename = os.path.split(video_path)

    if debug:
        debug_frame_dir = os.path.join(video_dir, "tmp_debug_frame")
        print(f"Debug frame output directory: {os.path.abspath(debug_frame_dir)}")
        if os.path.exists(debug_frame_dir):
            shutil.rmtree(debug_frame_dir)
        os.makedirs(debug_frame_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Cannot open video file.")
        return
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_width, frame_height = get_video_resolution(video_path)
    if frame_width is None or frame_height is None:
        print("Error: Unable to determine video resolution using FFmpeg.")
        cap.release()
        return
    
    preset_key = is_valid_aspect_ratio(frame_width, frame_height)
    if preset_key is None:
        print("Error: Unsupported aspect ratio.")
        cap.release()
        return
    preset = CONFIG_PRESETS[preset_key]
    
    reference_path = os.path.abspath(KUROYURI_PATH)
    print(f"Using reference image at: {reference_path}")
    if not os.path.exists(reference_path):
        print(f"Error: Reference image not found at: {reference_path}")
        cap.release()
        return
    
    reference_image = cv2.imread(reference_path, cv2.IMREAD_GRAYSCALE)
    
    DEFAULT_WIDTH = preset["DEFAULT_WIDTH"]
    DEFAULT_HEIGHT = preset["DEFAULT_HEIGHT"]
    
    YURI_X1_RATIO = preset["YURI_X1_RATIO"]
    YURI_Y1_RATIO = preset["YURI_Y1_RATIO"]
    YURI_X2_RATIO = preset["YURI_X2_RATIO"]
    YURI_Y2_RATIO = preset["YURI_Y2_RATIO"]

    SLIDE_X1_RATIO = preset["SLIDE_X1_RATIO"]
    SLIDE_Y1_RATIO = preset["SLIDE_Y1_RATIO"]
    SLIDE_X2_RATIO = preset["SLIDE_X2_RATIO"]
    SLIDE_Y2_RATIO = preset["SLIDE_Y2_RATIO"]

    x1, y1 = int(YURI_X1_RATIO * frame_width), int(YURI_Y1_RATIO * frame_height)
    x2, y2 = int(YURI_X2_RATIO * frame_width), int(YURI_Y2_RATIO * frame_height)
    
    frame_count = 0
    similarities = []
    high_similarity_intervals = []
    active_interval = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        time_stamp = frame_count / fps
        cropped_frame = frame[y1:y2, x1:x2]
        sharpened_frame = enhance_sharpness(cropped_frame)
        binary_frame = binarize_image(sharpened_frame)
        
        if debug:
            frame_filename = os.path.join(output_dir, f"{frame_count:06d}.png")
            cv2.imwrite(frame_filename, binary_frame)
        
        similarity = compute_similarity(binary_frame, reference_image)
        similarities.append([frame_count, similarity])
        
        frame_count += 1
    
    cap.release()

    # Determine dynamic threshold
    similarity_values = [sim for _, sim in similarities]
    max_sim = max(similarity_values)
    peak_threshold = max_sim * THRESHOLD_RATIO

    # Identify peak intervals
    peak_intervals = []
    start_frame = None
    for frame_num, sim in similarities:
        if sim >= peak_threshold:
            if start_frame is None:
                start_frame = frame_num
        else:
            if start_frame is not None:
                end_frame = frame_num - 1
                peak_intervals.append((start_frame, end_frame))
                start_frame = None
    if start_frame is not None:
        peak_intervals.append((start_frame, frame_count - 1))

    # Convert frame numbers to time
    fps = cap.get(cv2.CAP_PROP_FPS) if cap.isOpened() else fps
    peak_intervals_sec = [(start / fps, end / fps) for start, end in peak_intervals]

    # Pair peak intervals
    high_similarity_intervals = []
    i = 0
    while i < len(peak_intervals_sec):
        if i + 1 < len(peak_intervals_sec):
            start1, end1 = peak_intervals_sec[i]
            start2, end2 = peak_intervals_sec[i + 1]
            if start2 - end1 <= 1.0:  # max allowed gap between peaks
                high_similarity_intervals.append((start1, end2))
                i += 2
                continue

        # !The remaining lines in the while-loop is for handling edge cases
        # !Not thoroughly tested since it hardly occurs
        
        # Check if current peak is isolated
        prev_gap = float('inf') if i == 0 else peak_intervals_sec[i][0] - peak_intervals_sec[i - 1][1]
        next_gap = float('inf') if i == len(peak_intervals_sec) - 1 else peak_intervals_sec[i + 1][0] - peak_intervals_sec[i][1]
        
        if prev_gap > 2.0 and next_gap > 2.0:
            start, end = peak_intervals_sec[i]
            high_similarity_intervals.append((start, end))  # Treat as self-contained interval
            print(f"unpaired peak at {start:.2f} - {end:.2f} was treated as a self-contained interval")
        elif (prev_gap > 2.0 or next_gap > 2.0) and prev_gap > 1.0 and next_gap > 1.0:
            start, end = peak_intervals_sec[i]
            print(f"unpaired peak after seq{i} at {start:.2f} - {end:.2f} was skipped for it is not isolated")
        i += 1

    if debug:
        csv_path = os.path.join(output_dir, "_a.csv")
        with open(csv_path, mode="w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Frame", "Similarity"])
            writer.writerows(similarities)

    video_dir, video_filename = os.path.split(video_path)
    video_name, _ = os.path.splitext(video_filename)
    subtitle_path = os.path.join(video_dir, f"{video_name}.srt")
    with open(subtitle_path, "w") as sub_file:
        seq = 1
        prev_end = 0.0
        for interval in high_similarity_intervals:
            curr_end = interval[1]

            # Shift the start time slightly after the previous end (except for the first interval)
            adjusted_start = prev_end + 0.05 if prev_end > 0 else prev_end

            start_str = f"{int(adjusted_start // 3600):02}:{int((adjusted_start % 3600) // 60):02}:{int(adjusted_start % 60):02},{int((adjusted_start % 1) * 1000):03}"
            end_str = f"{int(curr_end // 3600):02}:{int((curr_end % 3600) // 60):02}:{int(curr_end % 60):02},{int((curr_end % 1) * 1000):03}"

            sub_file.write(f"{seq}\n")
            sub_file.write(f"{start_str} --> {end_str}\n")
            sub_file.write(f"{seq:04d}\n\n")

            prev_end = curr_end
            seq += 1
    
    if slides:
        slides_dir = os.path.join(video_dir, f"{video_name}-slides")
        if os.path.exists(slides_dir):
            shutil.rmtree(slides_dir)
        os.makedirs(slides_dir, exist_ok=True)

        for seq, (start_time, end_time) in enumerate(high_similarity_intervals, start=1):
            frame_target = int(start_time * fps) + 2
            cap = cv2.VideoCapture(video_path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_target)
            ret, frame = cap.read()
            if ret:
                x1_s, y1_s = int(SLIDE_X1_RATIO * frame_width), int(SLIDE_Y1_RATIO * frame_height)
                x2_s, y2_s = int(SLIDE_X2_RATIO * frame_width), int(SLIDE_Y2_RATIO * frame_height)
                slide_frame = frame[y1_s:y2_s, x1_s:x2_s]
                slide_path = os.path.join(slides_dir, f"{seq:04d}.png")
                cv2.imwrite(slide_path, slide_frame)
            cap.release()
    
    print(f"Extracted {frame_count} frames, and generated subtitles at {subtitle_path}")
    if debug:
        print(f"Saved frame images and similarity data at {output_dir}")

if __name__ == "__main__":
    args = parse_args()
    extract_frames(args.input, args.debug, args.slides)
