"""
YouTube 채널 관련 API 유틸 모듈

이 모듈의 책임(채널 레벨):
1) handle(@ 뒤 문자열) -> channelId
2) channelId -> uploads playlistId
3) uploads playlistId -> 채널 업로드 영상 목록(video_id/title/published_at)

주의:
- .env 로드는 여기서 하지 않는다. (노트북에서 load_dotenv() 1회)
- API Key는 환경변수(YOUTUBE_API_KEY)에서만 읽는다.
"""

import os
import time
import requests


def _get_api_key() -> str:
    """
    환경변수에서 API Key를 가져오고, 없으면 즉시 에러를 발생시킨다.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY not set. Check your .env and load_dotenv().")
    return api_key


def get_channel_id_from_handle(handle: str) -> str:
    """
    YouTube 채널 handle(@ 뒤 문자열)를 이용해 channelId를 조회한다.

    Parameters
    ----------
    handle : str
        유튜브 채널 핸들명 (@ 뒤 문자열)

    Returns
    -------
    str
        YouTube 채널 고유 ID (보통 'UC'로 시작)
    """
    api_key = _get_api_key()

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": handle,
        "type": "channel",
        "maxResults": 1,
        "key": api_key,
    }

    resp = requests.get(url, params=params, timeout=10)

    # HTTP 레벨 오류(쿼터 초과/권한 등) 빠르게 감지
    if resp.status_code != 200:
        raise RuntimeError(
            f"HTTP {resp.status_code} while fetching channelId for handle={handle} | {resp.text}"
        )

    data = resp.json()
    items = data.get("items", [])
    if not items:
        raise ValueError(f"Channel not found for handle: {handle}")

    # 검색 결과에서 channelId 추출
    return items[0]["snippet"]["channelId"]


def get_uploads_playlist_id(channel_id: str) -> str:
    """
    channelId를 기반으로 해당 채널의 uploads playlistId를 조회한다.
    uploads playlist에는 채널에 업로드된 모든 영상이 포함된다.

    Parameters
    ----------
    channel_id : str
        YouTube 채널 고유 ID (UC로 시작)

    Returns
    -------
    str
        uploads playlist ID
    """
    api_key = _get_api_key()

    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "contentDetails",   # uploads playlist 정보가 여기 들어있음
        "id": channel_id,
        "key": api_key,
    }

    resp = requests.get(url, params=params, timeout=10)
    if resp.status_code != 200:
        raise RuntimeError(
            f"HTTP {resp.status_code} while fetching uploads playlist for channel_id={channel_id} | {resp.text}"
        )

    data = resp.json()
    items = data.get("items", [])
    if not items:
        raise ValueError(f"No channel data found for channel_id={channel_id}")

    return items[0]["contentDetails"]["relatedPlaylists"]["uploads"]


def get_videos_from_uploads_playlist(
    uploads_playlist_id: str,
    channel_label: str,
    channel_handle: str,
    sleep_sec: float = 0.2,
) -> list[dict]:
    """
    uploads playlistId를 이용해 채널에 업로드된 모든 영상의 기본 메타를 수집한다.

    수집 컬럼:
    - channel_label
    - channel_handle
    - video_id
    - video_title
    - published_at

    Parameters
    ----------
    uploads_playlist_id : str
        채널 uploads playlist ID
    channel_label : str
        분석용 채널 라벨 (예: ISEGYE_IDOL)
    channel_handle : str
        채널 handle (@ 뒤 문자열)
    sleep_sec : float
        API 요청 간 대기 시간 (quota 안정성)

    Returns
    -------
    list[dict]
        채널의 모든 영상 기본 메타데이터 리스트
    """
    api_key = _get_api_key()

    videos: list[dict] = []
    page_token = None
    page_count = 0

    while True:
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {
            "part": "snippet",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,  # playlistItems API 최대
            "key": api_key,
        }

        if page_token:
            params["pageToken"] = page_token

        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code != 200:
            print(f"[WARN] HTTP {resp.status_code} for uploads_playlist_id={uploads_playlist_id}")
            break

        data = resp.json()
        items = data.get("items", [])
        if not items:
            break

        for item in items:
            snippet = item.get("snippet", {})
            resource = snippet.get("resourceId", {})

            video_id = resource.get("videoId")
            if not video_id:
                continue

            videos.append({
                "channel_label": channel_label,
                "channel_handle": channel_handle,
                "video_id": video_id,
                "video_title": snippet.get("title"),
                "published_at": snippet.get("publishedAt"),
            })

        page_count += 1
        print(f"[{channel_label}] page {page_count} | total videos: {len(videos)}")

        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(sleep_sec)

    return videos