# videos.py
"""
YouTube 영상(video) 관련 API 및 파생 로직

이 모듈의 책임:
1) 영상 duration(ISO 8601)을 초 단위로 변환
2) videos.list API를 이용한 batch 통계 수집 (최대 50개)
3) Shorts / Long 판별을 위한 기본 정보 제공

주의:
- 실행 코드 / print / DataFrame 생성 금지
- 분석 판단(Top-N 등)은 notebook에서 수행
"""

import os
import re
import requests
from typing import Optional


# --------------------------------------------------
# 내부 공용: API KEY 가져오기
# --------------------------------------------------
def _get_api_key() -> str:
    """
    환경변수에서 API Key를 가져오고, 없으면 즉시 에러를 발생시킨다.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY not set. Check your .env and load_dotenv().")
    return api_key


# --------------------------------------------------
# 영상 duration 파싱
# --------------------------------------------------
def parse_duration_to_seconds(duration: str) -> Optional[int]:
    """
    ISO 8601 형식의 YouTube duration을 초 단위로 변환한다.

    Examples
    --------
    - PT45S     -> 45
    - PT1M12S   -> 72
    - PT1H3M    -> 3780

    Parameters
    ----------
    duration : str
        YouTube contentDetails.duration 값

    Returns
    -------
    Optional[int]
        초 단위 영상 길이 (파싱 실패 시 None)
    """
    if not duration or not isinstance(duration, str):
        return None

    # ISO 8601 duration 패턴
    pattern = re.compile(
        r"PT"
        r"(?:(\d+)H)?"
        r"(?:(\d+)M)?"
        r"(?:(\d+)S)?"
    )

    match = pattern.match(duration)
    if not match:
        return None

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    return hours * 3600 + minutes * 60 + seconds


# --------------------------------------------------
# 리스트 분할 (batch 처리 보조)
# --------------------------------------------------
def chunked(lst: list[str], size: int = 50):
    """
    리스트를 size 단위로 나누어 generator로 반환한다.
    (YouTube videos.list API는 최대 50개까지 batch 허용)

    Parameters
    ----------
    lst : list[str]
        video_id 리스트
    size : int
        batch 크기 (기본 50)

    Yields
    ------
    list[str]
        분할된 video_id 리스트
    """
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


# --------------------------------------------------
# video statistics batch 수집
# --------------------------------------------------
def fetch_video_statistics_batch(video_ids: list[str]) -> dict[str, dict]:
    """
    여러 video_id를 batch로 받아 영상 통계 및 속성을 수집한다.

    수집 항목:
    - view_count
    - like_count
    - comment_count
    - duration_sec
    - video_type (SHORT / LONG / UNKNOWN)

    Parameters
    ----------
    video_ids : list[str]
        video_id 리스트 (최대 50개)

    Returns
    -------
    dict[str, dict]
        {
            video_id: {
                view_count: int,
                like_count: int,
                comment_count: int,
                duration_sec: Optional[int],
                video_type: str
            }
        }
    """
    if not video_ids:
        return {}

    api_key = _get_api_key()

    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "statistics,contentDetails",
        "id": ",".join(video_ids),  # ⭐ batch 핵심
        "key": api_key,
    }

    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(
            f"HTTP {resp.status_code} while fetching video statistics | {resp.text}"
        )

    data = resp.json()
    stats_map: dict[str, dict] = {}

    for item in data.get("items", []):
        video_id = item["id"]

        statistics = item.get("statistics", {})
        content = item.get("contentDetails", {})

        # 숫자형 통계 (없을 경우 0)
        view_count = int(statistics.get("viewCount", 0))
        like_count = int(statistics.get("likeCount", 0))
        comment_count = int(statistics.get("commentCount", 0))

        # 영상 길이
        duration = content.get("duration")
        duration_sec = parse_duration_to_seconds(duration)

        # Shorts / Long 판별 (60초 기준)
        if duration_sec is None:
            video_type = "UNKNOWN"
        elif duration_sec < 60:
            video_type = "SHORT"
        elif duration_sec < 1200:   # 20분 미만
            video_type = "LONG"
        else:
            video_type = "STREAM"

        stats_map[video_id] = {
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "duration_sec": duration_sec,
            "video_type": video_type,
        }

    return stats_map
