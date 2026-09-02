import sys

from pathlib import Path
from scene_split import split_video_into_scenes
from transcribe import get_json_transcription, write_scene_trancript
from Scene import SceneMetaData

DEFAULT_THRESHOLD = 5.0

def process_scenes(scenes):
    for scene in scenes:
        scene.transcript = get_json_transcription(scene.video_path)
        scene.transcript_output_path = write_scene_trancript(scene)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            f"Usage: process_tape.py <video_path> <output path> [optional threshold]"
        )
        sys.exit(1)
    threshold = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_THRESHOLD
    scenes = split_video_into_scenes(Path(sys.argv[1]), Path(sys.argv[2]), threshold)
    process_scenes(scenes)
    print(f"Split {sys.argv[1]} into {len(scenes)} clips and transcribed them")
