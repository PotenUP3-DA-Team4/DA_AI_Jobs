import requests
import os
import time

# 특정 영상의 모든 댓글을 YouTube Data API로 가능한 범위까지 수집하는 함수
def fetch_all_comments(video_id, sleep_sec=0.2):
    comments = []           # 수집된 모든 댓글을 저장할 리스트
    page_token = None       # pagination을 위한 페이지 토큰
    page_count = 0          # 수집된 페이지 수 (로그/디버깅용)

    # 다음 페이지가 없을 때까지 반복
    while True:
        # commentThreads API 요청 파라미터 설정
        params = {
            "part": "snippet",
            "videoId": video_id,
            "maxResults": 100,              # API에서 허용하는 최대 댓글 수
            "order": "time",                # 최신 댓글 순으로 조회
            "textFormat": "plainText",
            "key": os.getenv("YOUTUBE_API_KEY")
        }

        # 다음 페이지가 존재할 경우 pageToken 추가
        if page_token:
            params["pageToken"] = page_token

        # 댓글 조회 API 요청
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/commentThreads",
            params=params
        )

        # API 응답을 JSON 형태로 변환
        data = resp.json()

        # 댓글 비활성화, 삭제 영상, 권한 문제 등 오류 처리
        if "error" in data:
            print(f"[WARN] skip video_id={video_id}")
            break

        # 현재 페이지의 댓글 목록 추출    
        items = data.get("items", [])

        # 더 이상 댓글이 없으면 반복 종료
        if not items:
            break
        
        # 각 댓글(thread)의 top-level comment 추출
        for item in items:
            top = item["snippet"]["topLevelComment"]
            snippet = top["snippet"]

            # 댓글 메타데이터 저장
            comments.append({
                "video_id": video_id,
                "comment_id": top["id"],
                "comment_text": snippet["textDisplay"],
                "like_count": snippet["likeCount"],
                "published_at": snippet["publishedAt"]
            })

        # 수집 진행 상황 로그 출력
        page_count += 1
        print(f"page {page_count} | total comments: {len(comments)}")

        # 다음 페이지 토큰 추출
        page_token = data.get("nextPageToken")

        # 다음 페이지가 없으면 반복 종료
        if not page_token:
            break
        
        # API quota 및 요청 안정성을 위한 대기        
        time.sleep(sleep_sec)
        
    # 수집된 모든 댓글 반환
    return comments
