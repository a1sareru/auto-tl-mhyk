import argparse
import os
import shutil
import cv2
import numpy as np
import csv

def parse_args():
    parser = argparse.ArgumentParser(description="Extract frames from video, apply sharpening, binarization, and compute similarity with reference image.")
    parser.add_argument("--input", type=str, required=True, help="Path to the input video file.")
    parser.add_argument("--output", type=str, default="tmp-frame", help="Output directory for extracted frames and similarity results.")
    return parser.parse_args()

def is_valid_aspect_ratio(width, height):
    return abs((width / height) - (9 / 16)) < 0.05

def enhance_sharpness(image):
    # Stronger sharpening kernel
    kernel = np.array([[-1, -1, -1],
                       [-1, 9, -1],
                       [-1, -1, -1]])
    sharpened = cv2.filter2D(image, -1, kernel)
    return sharpened

def binarize_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary

def compute_similarity(image1, image2):
    # Resize images to match dimensions
    image2_resized = cv2.resize(image2, (image1.shape[1], image1.shape[0]))
    # Compute absolute difference
    diff = cv2.absdiff(image1, image2_resized)
    # Compute similarity as inverse of normalized difference sum
    similarity = 1 - (np.sum(diff) / (255 * image1.shape[0] * image1.shape[1]))
    return similarity

def extract_frames(video_path, output_dir):
    # Clear output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Cannot open video file.")
        return
    
    # Get video properties
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if not is_valid_aspect_ratio(frame_width, frame_height):
        print("Error: Video does not have a 9:16 aspect ratio.")
        cap.release()
        return
    
    # Load reference image
    reference_path = os.path.join(os.path.dirname(__file__), "kuroyuri.png")
    if not os.path.exists(reference_path):
        print("Error: Reference image 'kuroyuri.png' not found in script directory.")
        cap.release()
        return
    
    reference_image = cv2.imread(reference_path, cv2.IMREAD_GRAYSCALE)
    
    # Scale coordinates based on input video resolution
    scale_x = frame_width / 1080
    scale_y = frame_height / 1920
    
    x1, y1 = int(942 * scale_x), int(1554 * scale_y)
    x2, y2 = int(1015 * scale_x), int(1634 * scale_y)
    
    frame_count = 0
    similarities = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        cropped_frame = frame[y1:y2, x1:x2]
        sharpened_frame = enhance_sharpness(cropped_frame)
        binary_frame = binarize_image(sharpened_frame)
        frame_filename = os.path.join(output_dir, f"{frame_count:06d}.png")
        cv2.imwrite(frame_filename, binary_frame)
        
        similarity = compute_similarity(binary_frame, reference_image)
        similarities.append([frame_filename, similarity])
        
        frame_count += 1
    
    cap.release()
    
    # Save similarity results to CSV
    csv_path = os.path.join(output_dir, "a.csv")
    with open(csv_path, mode="w", newline="") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Frame", "Similarity"])
        writer.writerows(similarities)
    
    print(f"Extracted {frame_count} frames and saved similarity scores to {csv_path}")

if __name__ == "__main__":
    args = parse_args()
    extract_frames(args.input, args.output)
