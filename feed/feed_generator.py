import json
import os
from typing import Union, Any, List

from reels.reel import Reel


class FeedGenerator:
    reel_data = None
    
    def __init__(self):
        # Get the base directory (parent of feed directory)
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reels_json_path = os.path.join(base_dir, "data", "reels.json")
        self.base_dir = base_dir
        
        # Load reels data with error handling
        try:
            if os.path.exists(reels_json_path):
                with open(reels_json_path, 'r') as f:
                    self.reel_data = json.load(f)
            else:
                # If file doesn't exist, use empty dict
                self.reel_data = {}
        except Exception as e:
            # Log error but don't crash
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error loading reels.json: {str(e)}")
            self.reel_data = {}
    
    def _get_video_url(self, video_filename: str, remote_url: str) -> str:
        """
        Check if local video exists, return local URL if available, otherwise return remote URL.
        
        Args:
            video_filename: Name of the video file (e.g., "video6.mp4")
            remote_url: Remote URL from the JSON data
            
        Returns:
            URL to use for the video (local or remote)
        """
        # Check if local video file exists
        local_video_path = os.path.join(self.base_dir, "data", "reels", video_filename)
        if os.path.exists(local_video_path):
            # Return local URL that will be served by Flask
            return f"/videos/{video_filename}"
        # Fall back to remote URL if local file doesn't exist
        return remote_url

    def generate_feed(self, user_profile: Union[Any | dict] = None) -> List[Reel]:
        """
        Generate a feed of reels for the user.
        
        Args:
            user_profile: Optional user profile for personalized feed
            
        Returns:
            List of Reel objects
        """
        feed: List[Reel] = []

        for video, video_info in self.reel_data.items():
            # Extract influencer info if available, otherwise use default
            influencer = video_info.get('influencer', {
                'name': 'Fashion Influencer',
                'username': '@fashionista',
                'avatar': 'https://ui-avatars.com/api/?name=Fashion+Influencer&background=random'
            })
            
            # Get video URL (prefer local if available)
            video_url = self._get_video_url(video, video_info.get('url', ''))
            
            video_blob = Reel(
                id=video_info['id'],
                products=video_info['products'],
                shortDescription=video_info['shortDescription'],
                longDescription=video_info['description'],
                url=video_url,
                hashtags=video_info['hashtags'],
                influencer=influencer
            )
            feed.append(video_blob)
        return feed

