import json
from typing import Union, Any

from reels.reel import Reel


class FeedGenerator:
    reel_data = None
    with open("./data/reels.json", 'r') as f:
        reel_data = json.load(f)

    def __init__(self):
        pass

    def generate_feed(self, user_profile: Union[Any | dict]) -> list[Reel]:
        feed: list[Reel] = []

        for video, video_info in self.reel_data.items():
            video_blob = Reel(id=video_info['id'],
                              products=video_info['products'],
                              shortDescription=video_info['shortDescription'],
                              longDescription=video_info['description'],
                              url=video_info['url'],
                              hashtags=video_info['hashtags']
                              )
            feed.append(video_blob)
        return feed

