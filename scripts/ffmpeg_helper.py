from scenedetect import open_video, SceneManager, split_video_ffmpeg
from scenedetect.detectors import ContentDetector
import ffmpeg
from pathlib import Path
from PIL import Image

class FfmpegHelper:
    @staticmethod
    def get_scene_bounds(video_path, threshold):
        video = open_video(video_path)
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))

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

    # box = (left, top, right, bottom) in pixels"""
    def crop_date_overlay(image_path, output_path, box=(650, 650, 1080, 725)):
        img = Image.open(image_path)
        cropped = img.crop(box)
        cropped.save(output_path)
        return cropped
