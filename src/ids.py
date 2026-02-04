# ids.py
"""
YouTube URL에서 video_id를 추출하는 유틸 모듈

지원 형태:
- https://www.youtube.com/watch?v=VIDEO_ID
- https://youtu.be/VIDEO_ID
- https://www.youtube.com/watch?v=VIDEO_ID&list=...
"""

from urllib.parse import urlparse, parse_qs
from typing import Optional


def extract_video_id(url: str) -> Optional[str]:
    """
    YouTube URL에서 video_id를 추출한다.

    Parameters
    ----------
    url : str
        YouTube 영상 URL

    Returns
    -------
    Optional[str]
        video_id (추출 실패 시 None)
    """
    if not url or not isinstance(url, str):
        return None

    parsed = urlparse(url)

    # youtu.be 형태
    if parsed.netloc == "youtu.be":
        return parsed.path.lstrip("/")

    # youtube.com/watch 형태
    if "youtube.com" in parsed.netloc:
        query = parse_qs(parsed.query)
        return query.get("v", [None])[0]

    return None
