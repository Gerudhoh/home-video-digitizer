class SceneMetaData:
    def __init__(self, 
                 parent_video_path,     # Path to the video in which this scene occurs
                 video_timestamp,       # The time in the video this occurs
                 extracted_datetime     # The date and time the scene was recorded
                 ):
        self.video_path = parent_video_path
        self.timestamp = video_timestamp
        self.datetime = extracted_datetime

    def get_screenshot_name(self):
        scenes_dir = self.video_path.parent / "scenes" / "screenshots"
        output_name = f"{str(self.video_path.name).split('.')[0]}-scene{str(self.timestamp).split('.')[0]}.jpg"
        return scenes_dir / output_name

    def __str__(self):
        return f""" 
            Found in video {self.video_path} at {self.timestamp}
            Recorded on {self.datetime or "?"}
        """

    def __repr__(self):
        return f"Scene from {self.video_path} at {self.timestamp} on {self.datetime or "? date"}"