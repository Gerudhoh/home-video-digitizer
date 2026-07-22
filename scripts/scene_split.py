import sys

from pathlib import Path
from ffmpeg_helper import FfmpegHelper
from ocr_helper import OCR

DEFAULT_THRESHOLD = 80.5

def create_scene_screenshot_path(video_path, timestamp):
    scenes_dir = video_path.parent / "scenes" / "screenshots"
    output_name = f"{str(video_path.name).split('.')[0]}-scene{str(timestamp).split('.')[0]}.jpg"

    return scenes_dir / output_name

def capture_scene_start(video_path, scene_list):
    scene_screenshots = []
    scene_screenshot_dir = create_scene_screenshot_path(video_path, scene_list[0][0])
    scene_screenshot_dir.parent.mkdir(parents=True, exist_ok=True)
    for scene in scene_list:
        timestamp = scene[0]
        scene_screenshot_path = str(create_scene_screenshot_path(video_path, timestamp))
       
        if FfmpegHelper.try_extract_frame(video_path, scene_screenshot_path, timestamp):
            FfmpegHelper.crop_date_overlay(scene_screenshot_path, scene_screenshot_path)
            scene_screenshots.append(scene_screenshot_path)
    
    return scene_screenshots

def get_image_text(image_name):
    return OCR.extract_text(image_name)

def perform_ocr_on_scenes(scene_screenshots):
    scene_text = {}
    for scene in scene_screenshots:
        text = get_image_text(scene)
        scene_text[scene] = OCR.extract_date(text)
    
    return scene_text

def split_video_into_scenes(video_path, output_path, threshold):
    scene_list = FfmpegHelper.get_scene_bounds(video_path, threshold)
    scene_screenshots = capture_scene_start(video_path, scene_list)
    ocr_output_by_scene = perform_ocr_on_scenes(scene_screenshots)

    # If the dates don't exist:  
    #  Split as recomended 
    #
    # If the dates exist:
    #  If the date is different from the previous and next, SPLIT
    #  If the date is the same, NO SPLIT

    # split_video_ffmpeg(video_path, scene_list, output_path, show_progress=True)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            f"Usage: scene_split.py <video_path> <output path> [optional threshold]"
        )
        sys.exit(1)
    threshold = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_THRESHOLD
    split_video_into_scenes(Path(sys.argv[1]), Path(sys.argv[2]), threshold)
