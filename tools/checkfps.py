import cv2
import ffmpeg
import argparse
import os


def get_fps_opencv(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("[OpenCV] Error: Failed to open video file.")
        return None
    fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    return fps


def get_fps_ffmpeg(video_path):
    try:
        probe = ffmpeg.probe(video_path)
        for stream in probe['streams']:
            if stream['codec_type'] == 'video':
                r_frame_rate = stream['r_frame_rate']
                num, denom = map(int, r_frame_rate.split('/'))
                return num / denom
    except Exception as e:
        print(f"[FFmpeg] Error getting FPS: {e}")
    return None


def main():
    parser = argparse.ArgumentParser(description="Check video FPS using OpenCV and FFmpeg.")
    parser.add_argument("video", type=str, help="Path to the video file")
    args = parser.parse_args()

    video_path = args.video
    if not os.path.exists(video_path):
        print(f"Error: Video file does not exist at {video_path}")
        return

    print(f"Checking FPS for video: {video_path}")

    fps_opencv = get_fps_opencv(video_path)
    if fps_opencv:
        print(f"[OpenCV] FPS: {fps_opencv:.4f}")
    else:
        print("[OpenCV] Failed to retrieve FPS.")

    fps_ffmpeg = get_fps_ffmpeg(video_path)
    if fps_ffmpeg:
        print(f"[FFmpeg] FPS: {fps_ffmpeg:.4f}")
    else:
        print("[FFmpeg] Failed to retrieve FPS.")


if __name__ == "__main__":
    main()
