from scenedetect import open_video, SceneManager, split_video_ffmpeg
from scenedetect.detectors import ContentDetector
import sys

DEFAULT_THRESHOLD = 80.5

def split_video_into_scenes(video_path, output_path, threshold):
    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    
    scene_manager.detect_scenes(video, show_progress=True)
    scene_list = scene_manager.get_scene_list()
    split_video_ffmpeg(video_path, scene_list, output_path, show_progress=True)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            f"Usage: scene_split.py <video_path> <output path> [optional threshold]"
        )
        sys.exit(1)
    threshold = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_THRESHOLD
    split_video_into_scenes(sys.argv[1], sys.argv[2], threshold)
