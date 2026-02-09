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
    # 🔧 scheme 없으면 보정
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    # youtu.be 형태
    if parsed.netloc in ("youtu.be", "www.youtu.be"):
        return parsed.path.lstrip("/")

    # youtube.com/watch 형태
    if parsed.netloc in ("youtube.com", "www.youtube.com"):
        query = parse_qs(parsed.query)
        return query.get("v", [None])[0]


    return None
