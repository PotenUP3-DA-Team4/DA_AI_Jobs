import os
import re
import requests
from typing import List, Dict, Optional

def parse_duration_to_seconds(duration: str) -> Optional[int]:
    """
    ISO 8601 형식의 YouTube duration을 초 단위로 변환
    예:
    - PT45S → 45
    - PT1M12S → 72
    - PT1H3M → 3780
    """
    if not duration or not isinstance(duration, str):
        return None
    
    pattern = re.compile(
        r'PT'
        r'(?:(\d+)H)?'
        r'(?:(\d+)M)?'
        r'(?:(\d+)S)?'
    )

    match = pattern.match(duration)
    if not match:
        return None

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    return hours * 3600 + minutes * 60 + seconds

def fetch_video_statistics_batch(video_ids: List[str]) -> Dict[str, Dict]:
    """
    여러 video_id를 batch로 받아
    조회수 / 좋아요 / 댓글 수 / 영상 길이 / 숏폼 여부를 반환

    Parameters
    ----------
    video_ids : list[str]
        video_id 리스트 (최대 50개)

    Returns
    -------
    dict
        {
          video_id: {
              view_count,
              like_count,
              comment_count,
              duration_sec,
              video_type
          }
        }
    """

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY not set")
    url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "statistics,contentDetails",
        "id": ",".join(video_ids),  # ⭐ batch 처리 핵심
        "key": api_key
    }

    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    stats_map = {}

    for item in data.get("items", []):
        vid = item["id"]

        statistics = item.get("statistics", {})
        content = item.get("contentDetails", {})

        # 조회수 / 좋아요 / 댓글 수
        view_count = int(statistics.get("viewCount", 0))
        like_count = int(statistics.get("likeCount", 0))
        comment_count = int(statistics.get("commentCount", 0))

        # 영상 길이 (숏폼 판단용)
        duration = content.get("duration")
        duration_sec = parse_duration_to_seconds(duration)

        # Shorts 판별
        if duration_sec is None:
            video_type = "UNKNOWN"
        elif duration_sec < 60:
            video_type = "SHORT"
        else:
            video_type = "LONG"

        stats_map[vid] = {
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "duration_sec": duration_sec,
            "video_type": video_type
        }

    return stats_map


def chunked(lst: List[str], size: int = 50):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


