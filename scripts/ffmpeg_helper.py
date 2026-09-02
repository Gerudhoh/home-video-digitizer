from scenedetect import open_video, SceneManager, split_video_ffmpeg
from scenedetect.detectors import AdaptiveDetector
import ffmpeg
from pathlib import Path
from PIL import Image

class FfmpegHelper:
    @staticmethod
    def get_scene_bounds(video_path, threshold, window_width=3, min_scene_len=30):
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(
            AdaptiveDetector(
                adaptive_threshold=threshold,
                window_width=window_width,
                min_scene_len=min_scene_len,
            )
        )

        scene_manager.detect_scenes(video, show_progress=True)
        return scene_manager.get_scene_list()

    @staticmethod
    def try_extract_frame(video_path, output_image_path, timestamp=5):
        try:
            (
                ffmpeg
                .input(video_path, ss=timestamp)
                .output(output_image_path, vframes=1, **{'q:v': 2})
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            return True
        except ffmpeg.Error as e:
            print(f"Error: {e.stderr.decode()}")
            return False

    # region = (left, top, right, bottom) as fractions (0-1) of the frame's
    # actual width/height, anchored to the bottom-right corner where camcorder
    # date overlays are burned in. Fractional so it scales across capture
    # resolutions instead of the fixed-pixel box this replaced, which only
    # ever matched one specific resolution and silently clipped to black on
    # any other.
    @staticmethod
    def crop_date_overlay(image_path, output_path, region=(0.5, 0.7, 1.0, 1.0)):
        img = Image.open(image_path)
        width, height = img.size
        left, top, right, bottom = region
        box = (
            int(left * width),
            int(top * height),
            int(right * width),
            int(bottom * height),
        )
        cropped = img.crop(box)
        cropped.save(output_path)
        return cropped
