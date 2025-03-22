import argparse
import os
import shutil
import cv2
import numpy as np
import csv
import ffmpeg
import re
import yaml

def load_config(config_path="config.yaml"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file '{config_path}' not found.")
    
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def parse_args():
    parser = argparse.ArgumentParser(description="Extract frames from video, apply sharpening, binarization, compute similarity with reference image, and generate subtitles.")
    parser.add_argument("--input", type=str, required=True, help="Path to the input video file.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode to save tmp_frame images.")
    parser.add_argument("--slides", action="store_true", help="Enable slides generation for high similarity intervals.")
    return parser.parse_args()

def is_valid_aspect_ratio(width, height):
    return abs((width / height) - (9 / 16)) < 0.05

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
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    config = load_config(config_path)

    DEFAULT_WIDTH = config["DEFAULT_WIDTH"]
    DEFAULT_HEIGHT = config["DEFAULT_HEIGHT"]

    CROP_X1_RATIO = config["CROP_X1_RATIO"]
    CROP_Y1_RATIO = config["CROP_Y1_RATIO"]
    CROP_X2_RATIO = config["CROP_X2_RATIO"]
    CROP_Y2_RATIO = config["CROP_Y2_RATIO"]

    SLIDE_X1_RATIO = config["SLIDE_X1_RATIO"]
    SLIDE_Y1_RATIO = config["SLIDE_Y1_RATIO"]
    SLIDE_X2_RATIO = config["SLIDE_X2_RATIO"]
    SLIDE_Y2_RATIO = config["SLIDE_Y2_RATIO"]

    output_dir = "tmp-frame"
    if debug:
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir)
        os.makedirs(output_dir, exist_ok=True)
    
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
    
    if not is_valid_aspect_ratio(frame_width, frame_height):
        print("Error: Video does not have a 9:16 aspect ratio.")
        cap.release()
        return
    
    reference_path = os.path.join(os.path.dirname(__file__), "kuroyuri.png")
    if not os.path.exists(reference_path):
        print("Error: Reference image 'kuroyuri.png' not found in script directory.")
        cap.release()
        return
    
    reference_image = cv2.imread(reference_path, cv2.IMREAD_GRAYSCALE)
    
    scale_x = frame_width / DEFAULT_WIDTH
    scale_y = frame_height / DEFAULT_HEIGHT
    
    x1, y1 = int(CROP_X1_RATIO * frame_width), int(CROP_Y1_RATIO * frame_height)
    x2, y2 = int(CROP_X2_RATIO * frame_width), int(CROP_Y2_RATIO * frame_height)
    
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
    peak_threshold = max_sim * 0.97

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

            start_str = f"{int(prev_end // 3600):02}:{int((prev_end % 3600) // 60):02}:{int(prev_end % 60):02},{int((prev_end % 1) * 1000):03}"
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
