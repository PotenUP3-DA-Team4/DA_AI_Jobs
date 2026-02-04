# comments.py
"""
YouTube 댓글(commentThreads) 수집 모듈

이 모듈의 책임:
- 특정 video_id에 대한 모든 top-level 댓글 수집
- pagination 처리
- 댓글 비활성화 / 오류 안전 처리

주의:
- 실행 코드 / DataFrame / CSV 저장 금지
- 분석 로직은 notebook에서 수행
"""

import os
import time
import requests
from typing import List, Dict


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
# 댓글 전체 수집
# --------------------------------------------------
def fetch_all_comments(
    video_id: str,
    sleep_sec: float = 0.2,
) -> List[Dict]:
    """
    특정 video_id에 대해 가능한 범위까지 모든 댓글을 수집한다.

    수집 대상:
    - top-level 댓글만 (reply 제외)
    - 최신 댓글부터 과거 댓글까지

    Parameters
    ----------
    video_id : str
        YouTube video ID
    sleep_sec : float
        API 요청 간 대기 시간 (quota 안정성)

    Returns
    -------
    List[Dict]
        댓글 메타데이터 리스트
        {
            video_id,
            comment_id,
            comment_text,
            like_count,
            published_at
        }
    """
    api_key = _get_api_key()

    comments: List[Dict] = []
    page_token = None
    page_count = 0

    while True:
        url = "https://www.googleapis.com/youtube/v3/commentThreads"
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,          # API 최대
            "order": "time",            # 최신 댓글 순
            "textFormat": "plainText",
            "key": api_key,
        }

        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(url, params=params, timeout=10)

        # HTTP 에러 (quota, 권한 등)
        if resp.status_code != 200:
            print(f"[WARN] HTTP {resp.status_code} for video_id={video_id}")
            break

        data = resp.json()

        # 댓글 비활성화 / 삭제 영상 / 권한 문제
        if "error" in data:
            print(f"[WARN] comments disabled or error for video_id={video_id}")
            break

        items = data.get("items", [])
        if not items:
            break

        for item in items:
            snippet = item.get("snippet", {})
            top = snippet.get("topLevelComment", {})
            comment_snippet = top.get("snippet", {})

            comments.append({
                "video_id": video_id,
                "comment_id": top.get("id"),
                "comment_text": comment_snippet.get("textDisplay"),
                "like_count": comment_snippet.get("likeCount"),
                "published_at": comment_snippet.get("publishedAt"),
            })

        page_count += 1
        print(f"[comments] video={video_id} | page {page_count} | total={len(comments)}")

        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(sleep_sec)

    return comments
