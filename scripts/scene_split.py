import sys

from pathlib import Path
from ffmpeg_helper import FfmpegHelper, split_video_ffmpeg
from ocr_helper import OCR
from Scene import SceneMetaData, scenes_to_timecode_pairs

DEFAULT_THRESHOLD = 5.0

def create_scene_metadata_list(raw_scene_list, video_path):
    scenes = []
    for raw_scene in raw_scene_list:
        scenes.append(
            SceneMetaData(
                parent_video_path=video_path,
                video_timestamp=raw_scene[0],
                video_timestamp_end=raw_scene[1],
                extracted_datetime=None
            )
        )

    return scenes

def capture_scene_start(scene_list):
    scene0 = scene_list[0]
    scene_screenshot_dir = scene0.get_screenshot_name()
    scene_screenshot_dir.parent.mkdir(parents=True, exist_ok=True)
    for scene in scene_list:
        scene_screenshot_path = str(scene.get_screenshot_name())
       
        if FfmpegHelper.try_extract_frame(scene.video_path, scene_screenshot_path, scene.timestamp):
            FfmpegHelper.crop_date_overlay(scene_screenshot_path, scene_screenshot_path)

def perform_ocr_on_scenes(scene_list):
    for scene in scene_list:
        text = OCR.extract_text(str(scene.get_screenshot_name()))
        scene.datetime = OCR.extract_date(text)

def split_video_into_scenes(video_path, output_path, threshold):
    raw_scene_list = FfmpegHelper.get_scene_bounds(video_path, threshold)
    if(len(raw_scene_list) > 1):
        scene_list = create_scene_metadata_list(raw_scene_list, video_path)
        capture_scene_start(scene_list)
        perform_ocr_on_scenes(scene_list)
        timecode_pairs = scenes_to_timecode_pairs(scene_list)
        print(scene_list)
        split_video_ffmpeg(video_path, timecode_pairs, output_path, show_progress=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            f"Usage: scene_split.py <video_path> <output path> [optional threshold]"
        )
        sys.exit(1)
    threshold = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_THRESHOLD
    split_video_into_scenes(Path(sys.argv[1]), Path(sys.argv[2]), threshold)
