"""
Video Fetcher Module
Downloads or fetches video files during server startup from various sources.
"""
import os
import json
import logging
import shutil
import requests
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class VideoFetcher:
    """Fetches videos from external storage during server startup."""
    
    def __init__(self, target_dir: str = None):
        """
        Initialize VideoFetcher.
        
        Args:
            target_dir: Directory where videos should be stored (default: data/reels/)
        """
        if target_dir is None:
            # Default to data/reels/ relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            target_dir = os.path.join(base_dir, "data", "reels")
        
        self.target_dir = target_dir
        self.ensure_target_dir()
    
    def ensure_target_dir(self):
        """Ensure the target directory exists."""
        os.makedirs(self.target_dir, exist_ok=True)
        logger.info(f"Video target directory: {self.target_dir}")
    
    def fetch_from_s3(self, s3_url: str, video_list: List[str]) -> int:
        """
        Fetch videos from S3-compatible storage.
        
        Args:
            s3_url: Base S3 URL (e.g., https://bucket.s3.region.amazonaws.com/videos/)
            video_list: List of video filenames to download
            
        Returns:
            Number of videos successfully downloaded
        """
        downloaded = 0
        for video_file in video_list:
            try:
                video_url = f"{s3_url.rstrip('/')}/{video_file}"
                target_path = os.path.join(self.target_dir, video_file)
                
                if os.path.exists(target_path):
                    logger.info(f"Video already exists, skipping: {video_file}")
                    downloaded += 1
                    continue
                
                logger.info(f"Downloading from S3: {video_url}")
                response = requests.get(video_url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(target_path, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
                
                logger.info(f"Downloaded: {video_file}")
                downloaded += 1
            except Exception as e:
                logger.error(f"Failed to download {video_file}: {str(e)}")
        
        return downloaded
    
    def fetch_from_url(self, base_url: str, video_list: List[str]) -> int:
        """
        Fetch videos from a remote URL.
        
        Args:
            base_url: Base URL for videos (e.g., https://example.com/videos/)
            video_list: List of video filenames to download
            
        Returns:
            Number of videos successfully downloaded
        """
        downloaded = 0
        for video_file in video_list:
            try:
                video_url = f"{base_url.rstrip('/')}/{video_file}"
                target_path = os.path.join(self.target_dir, video_file)
                
                if os.path.exists(target_path):
                    logger.info(f"Video already exists, skipping: {video_file}")
                    downloaded += 1
                    continue
                
                logger.info(f"Downloading from URL: {video_url}")
                response = requests.get(video_url, stream=True, timeout=60)
                response.raise_for_status()
                
                with open(target_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Downloaded: {video_file}")
                downloaded += 1
            except Exception as e:
                logger.error(f"Failed to download {video_file}: {str(e)}")
        
        return downloaded
    
    def fetch_from_local_path(self, source_path: str, video_list: List[str] = None) -> int:
        """
        Copy videos from a local path (external drive, network mount, etc.).
        
        Args:
            source_path: Source directory path
            video_list: Optional list of specific videos to copy (if None, copies all .mp4 files)
            
        Returns:
            Number of videos successfully copied
        """
        if not os.path.exists(source_path):
            logger.error(f"Source path does not exist: {source_path}")
            return 0
        
        copied = 0
        
        if video_list:
            # Copy specific videos
            for video_file in video_list:
                try:
                    source_file = os.path.join(source_path, video_file)
                    target_file = os.path.join(self.target_dir, video_file)
                    
                    if os.path.exists(target_file):
                        logger.info(f"Video already exists, skipping: {video_file}")
                        copied += 1
                        continue
                    
                    if os.path.exists(source_file):
                        shutil.copy2(source_file, target_file)
                        logger.info(f"Copied: {video_file}")
                        copied += 1
                    else:
                        logger.warning(f"Source file not found: {source_file}")
                except Exception as e:
                    logger.error(f"Failed to copy {video_file}: {str(e)}")
        else:
            # Copy all .mp4 files
            for file in os.listdir(source_path):
                if file.endswith(('.mp4', '.webm', '.mov', '.avi')):
                    try:
                        source_file = os.path.join(source_path, file)
                        target_file = os.path.join(self.target_dir, file)
                        
                        if os.path.exists(target_file):
                            continue
                        
                        shutil.copy2(source_file, target_file)
                        logger.info(f"Copied: {file}")
                        copied += 1
                    except Exception as e:
                        logger.error(f"Failed to copy {file}: {str(e)}")
        
        return copied
    
    def get_video_list_from_json(self, reels_json_path: str) -> List[str]:
        """
        Extract video filenames from reels.json.
        
        Args:
            reels_json_path: Path to reels.json file
            
        Returns:
            List of video filenames
        """
        video_list = []
        
        try:
            if os.path.exists(reels_json_path):
                with open(reels_json_path, 'r') as f:
                    reels_data = json.load(f)
                
                # Extract video filenames (keys in the JSON)
                video_list = [key for key in reels_data.keys() if key.endswith(('.mp4', '.webm', '.mov', '.avi'))]
                logger.info(f"Found {len(video_list)} videos in reels.json")
            else:
                logger.warning(f"reels.json not found at: {reels_json_path}")
        except Exception as e:
            logger.error(f"Error reading reels.json: {str(e)}")
        
        return video_list
    
    def fetch_videos(self) -> int:
        """
        Main method to fetch videos based on environment configuration.
        
        Checks environment variables in order:
        1. VIDEO_STORAGE_URL - Remote URL (S3, HTTP, etc.)
        2. VIDEO_STORAGE_PATH - Local path (external drive, network mount, Railway volume)
        
        For Railway: Set VIDEO_STORAGE_PATH=/data to use mounted volume
        
        Returns:
            Number of videos successfully fetched
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reels_json_path = os.path.join(base_dir, "data", "reels.json")
        
        # Get list of videos from reels.json
        video_list = self.get_video_list_from_json(reels_json_path)
        
        if not video_list:
            logger.warning("No videos found in reels.json, skipping fetch")
            return 0
        
        # Check for remote URL storage
        storage_url = os.environ.get('VIDEO_STORAGE_URL')
        if storage_url:
            logger.info(f"Fetching videos from URL: {storage_url}")
            parsed_url = urlparse(storage_url)
            
            if 's3' in parsed_url.netloc or 'amazonaws.com' in parsed_url.netloc:
                return self.fetch_from_s3(storage_url, video_list)
            else:
                return self.fetch_from_url(storage_url, video_list)
        
        # Check for local path storage (including Railway mounted volumes)
        storage_path = os.environ.get('VIDEO_STORAGE_PATH')
        if storage_path:
            logger.info(f"Fetching videos from local path: {storage_path}")
            # Check if path exists
            if not os.path.exists(storage_path):
                logger.warning(f"Storage path does not exist: {storage_path}")
                logger.info("Videos should be uploaded to this path before server starts")
                return 0
            return self.fetch_from_local_path(storage_path, video_list)
        
        logger.info("No VIDEO_STORAGE_URL or VIDEO_STORAGE_PATH set, skipping video fetch")
        return 0


def fetch_videos_on_startup():
    """
    Function to be called during app startup to fetch videos.
    This should be called before the Flask app starts serving requests.
    """
    try:
        logger.info("Starting video fetch process...")
        fetcher = VideoFetcher()
        count = fetcher.fetch_videos()
        logger.info(f"Video fetch completed. {count} videos available.")
        return count
    except Exception as e:
        logger.error(f"Error during video fetch: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 0
