from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.proxies import WebshareProxyConfig
import re
import os

def extract_video_id(url):
    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})"
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def fetch_transcript(youtube_url, save_as=None):
    video_id = extract_video_id(youtube_url)
    if not video_id:
        return None
    try:
        ytt_api = YouTubeTranscriptApi()
        fetched = ytt_api.fetch(video_id)
        full_text = "\n".join([entry.text for entry in fetched])
        if save_as:
            os.makedirs("data/raw", exist_ok=True)
            with open(f"data/raw/{save_as}.txt", "w", encoding="utf-8") as f:
                f.write(full_text)
        return full_text
    except Exception as e:
        print(f"error: {e}")
        return None