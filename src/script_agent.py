"""
Script Agent — 채널별 특화 대본 생성
"""
import anthropic
from pathlib import Path
from typing import Dict

client = anthropic.Anthropic()

CHANNEL_TONE = {
    "seowon": """
- 어투: 전문적·권위있음 (~입니다, ~했습니다)
- 속도: 분당 280자 (뉴스 앵커 속도)
- 금지: 구어체, 감탄사, 과장 표현
- 필수: 수치/법령 근거 포함
- 구조: 사례 → 원인 → 예방 → 대처 → 정리
""",
    "jusi": """
- 어투: 친근한 시니어 (~이에요, ~거든요)
- 속도: 분당 300자 (대화하듯 자연스럽게)
- 필수: 공감 표현, 실제 경험담 느낌
- 금지: 딱딱한 강의체
- 구조: 공감훅 → 경험담 → 핵심팁 → 응원
""",
    "unspoken": """
- 어투: 없음 (인트로 자막만, TTS 없음)
- 자막: 감성 영문 + 한글 병기
- 필수: 트랙 정보, 분위기 설명
- 구조: 무드 소개 → 트랙리스트 → 아웃트로
""",
}


class ScriptAgent:
    def __init__(self, channel: str, config: Dict, workspace: Path):
        self.channel = channel
        self.config = config
        self.workspace = workspace

    def run(self) -> Dict:
        concept_path = self.workspace / "concept.md"
        concept = concept_path.read_text(encoding="utf-8") if concept_path.exists() else ""

        print(f"  ✍️  SCRIPTWRITER: 대본 생성 중...")

        script = self._generate_script(concept)
        script_path = self.workspace / "script.md"
        script_path.write_text(script, encoding="utf-8")

        # scenes.md 생성 (씬 단위 분해)
        scenes = self._parse_scenes(script)
        scenes_path = self.workspace / "scenes.md"
        scenes_path.write_text(scenes, encoding="utf-8")

        print(f"  ✅ script.md + scenes.md 생성")
        return {"script_path": str(script_path), "scenes_path": str(scenes_path)}

    def _generate_script(self, concept: str) -> str:
        tone = CHANNEL_TONE.get(self.channel, "")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": f"""다음 컨셉을 바탕으로 유튜브 영상 대본을 작성하세요.

채널 톤 가이드:
{tone}

컨셉:
{concept}

대본 형식:
| 씬 | 나레이션 텍스트 | 이미지 키워드 | 자막 | 길이(초) |
|----|----------------|-------------|------|---------|

각 씬은 6~8초 단위로 구성하고,
전체 영상 길이는 채널별로:
- seowon: 5~8분 (롱폼)
- jusi: 3~5분 또는 60초 (쇼츠 우선)
- unspoken: 30분~1시간 (음악 전체)

마지막에 유튜브 설명란 초안도 포함하세요."""
            }],
        )
        return response.content[0].text

    def _parse_scenes(self, script: str) -> str:
        """스크립트를 씬 단위 JSON으로 분해"""
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": f"""다음 대본을 씬 단위 JSON 배열로 변환하세요.
각 항목: {{"scene": N, "text": "나레이션", "image_keyword": "이미지검색어", "subtitle": "자막", "duration": 초}}

대본:
{script[:3000]}

JSON 배열만 출력하세요. 마크다운 코드블록 없이."""
            }],
        )
        return response.content[0].text
