# fetches commentary transcript from any youtube video link
# install first: pip install youtube-transcript-api

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import os
import re

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

def extract_video_id(url):
    # handles both youtube.com/watch?v=xxx and youtu.be/xxx formats
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
        print("could not extract video ID from URL")
        return None

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        # join all text chunks into one string
        full_text = "\n".join([entry["text"] for entry in transcript])

        if save_as:
            os.makedirs("data/raw", exist_ok=True)
            filepath = f"data/raw/{save_as}.txt"
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(full_text)
            print(f"saved transcript to {filepath}")

        return full_text

    except TranscriptsDisabled:
        print("transcripts are disabled for this video")
        return None
    except NoTranscriptFound:
        print("no transcript found — try a different video")
        return None
    except Exception as e:
        print(f"error: {e}")
        return None

if __name__ == "__main__":
    # test it with any football match youtube URL
    url = input("paste youtube URL: ")
    text = fetch_transcript(url, save_as="youtube_match")
    if text:
        print(f"fetched {len(text)} characters")
        print("\nfirst 500 chars preview:")
        print(text[:500])