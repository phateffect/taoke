import os
import requests
import time
# import whisper

from contextlib import contextmanager
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, AnyHttpUrl, Json
from scenedetect import detect, open_video, save_images, AdaptiveDetector

from .constants import UA, REF


session = requests.session()
session.headers["user-agent"] = UA
session.headers["referer"] = REF


class FeedContent(BaseModel):
    cover_url: AnyHttpUrl = Field(alias="banner")
    video_url: AnyHttpUrl = Field(alias="playUrl")

    def get(self, attr, download=False):
        url = getattr(self, f"{attr}_url")
        ext = Path(url.path).suffix
        path = Path(f"{attr}{ext}")
        if download:
            resp = session.get(str(url))
            path.write_bytes(resp.content)
        return path.name


class Feed(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: int = Field(alias="feedId")
    title: str
    summary: str = Field(alias="summart")
    content: Json[FeedContent] = Field(exclude=True)

    @classmethod
    def model_validate_feed_id(cls, feed_id):
        resp = session.post(
            "https://qngateway.taobao.com/gw/invoke/circles.pc.feed.get",
            data={"feed_id": feed_id, "timestamp": int(time.time() * 1000)},
        )
        return cls.model_validate(resp.json())

    def split_scenes(self):
        video_path = self.content.get("video")
        scene_list = detect(video_path, AdaptiveDetector(), show_progress=True)
        video = open_video(video_path)
        save_images(
            scene_list,
            video,
            num_images=1,
            image_name_template="$VIDEO_NAME-$SCENE_NUMBER",
            image_extension="png",
            output_dir="slides"
        )

    def asr(self):
        video_path = self.content.get("video")
        model = whisper.load_model("medium")
        result = model.transcribe(
            video_path,
            verbose=False,
            initial_prompt=f"这是关于淘宝电商的分享 主题是: {self.title}",
            language="zh"
        )
        return result

    def render_html(self):
        pass

    @contextmanager
    def working_dir(self):
        new_dir = Path(f"data/{self.id}")
        new_dir.mkdir(parents=True, exist_ok=True)
        cwd = Path.cwd()
        os.chdir(new_dir)
        try:
            yield
        finally:
            os.chdir(cwd)
