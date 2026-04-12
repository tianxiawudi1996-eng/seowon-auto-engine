"""
YouTube Uploader — YouTube Data API v3 자동 업로드
"""
import json
from pathlib import Path
from typing import Dict


CHANNEL_SETTINGS = {
    "seowon": {
        "category_id": "28",     # 과학기술
        "default_tags": ["건설안전", "산업재해", "안전교육", "건설현장", "SAFE"],
        "privacy": "public",
        "playlist": "건설 안전 교육",
    },
    "jusi": {
        "category_id": "26",     # 방법/스타일
        "default_tags": ["직장인", "시니어조언", "커리어", "주니어", "쥬시톡"],
        "privacy": "public",
        "playlist": "시니어 경험 전수",
    },
    "unspoken": {
        "category_id": "10",     # 음악
        "default_tags": ["감성음악", "AI음악", "플레이리스트", "힐링", "인디"],
        "privacy": "public",
        "playlist": "말하지 않는 것들",
    },
}


class YouTubeUploader:
    def __init__(self, channel: str, workspace: Path, output: Path):
        self.channel = channel
        self.workspace = workspace
        self.output = output
        self.settings = CHANNEL_SETTINGS[channel]

    def prepare_metadata(self) -> Dict:
        """업로드용 메타데이터 생성 (seo_optimizer.py 연동)"""
        concept_path = self.workspace / "concept.md"
        concept = concept_path.read_text(encoding="utf-8") if concept_path.exists() else ""

        # 메타데이터 JSON 생성
        import anthropic
        client = anthropic.Anthropic()

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": f"""다음 컨셉으로 YouTube 업로드 메타데이터를 JSON으로 생성하세요.

채널: {self.channel}
기본 태그: {', '.join(self.settings['default_tags'])}

컨셉:
{concept[:1000]}

JSON 형식 (마크다운 없이):
{{
  "title": "제목 (60자 이내, SEO 최적화)",
  "description": "설명 (첫 2줄이 핵심, 500자)",
  "tags": ["태그1", "태그2", ...최대 15개],
  "thumbnail_text": "썸네일 메인 문구 (20자 이내)"
}}"""
            }],
        )

        try:
            metadata = json.loads(response.content[0].text)
        except json.JSONDecodeError:
            metadata = {
                "title": "제목 생성 실패",
                "description": "",
                "tags": self.settings["default_tags"],
                "thumbnail_text": "",
            }

        # 태그 합치기
        metadata["tags"] = list(set(
            metadata.get("tags", []) + self.settings["default_tags"]
        ))[:15]
        metadata["categoryId"] = self.settings["category_id"]
        metadata["privacyStatus"] = self.settings["privacy"]

        # youtube_meta.json 저장
        meta_path = self.output / "youtube_meta.json"
        meta_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"  ✅ youtube_meta.json 생성")
        return metadata

    def upload(self, video_path: Path, metadata: Dict) -> str:
        """YouTube API v3로 실제 업로드"""
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            from google.oauth2.credentials import Credentials

            # TODO: OAuth2 토큰 설정 필요
            creds = Credentials.from_authorized_user_file("token.json")
            youtube = build("youtube", "v3", credentials=creds)

            request = youtube.videos().insert(
                part="snippet,status",
                body={
                    "snippet": {
                        "title": metadata["title"],
                        "description": metadata["description"],
                        "tags": metadata["tags"],
                        "categoryId": metadata["categoryId"],
                    },
                    "status": {"privacyStatus": metadata["privacyStatus"]},
                },
                media_body=MediaFileUpload(str(video_path), chunksize=-1, resumable=True),
            )

            response = request.execute()
            video_id = response["id"]
            print(f"  ✅ YouTube 업로드 완료: https://youtube.com/watch?v={video_id}")
            return video_id

        except ImportError:
            print("  ⚠️  google-api-python-client 미설치. pip install google-api-python-client")
            return ""
        except Exception as e:
            print(f"  ⚠️  업로드 실패: {e}")
            return ""
