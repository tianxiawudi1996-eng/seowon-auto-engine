"""
SEOWON-AUTO ENGINE v1.0
========================
"영상 만들어줘" 한마디로 완성되는 3채널 자동 영상 생성 시스템

채널:
  - seowon  : 서원토건 공식 (안전교육·현장실무)
  - jusi    : 쥬시톡 (시니어→주니어 경험 전수)
  - unspoken: 말하지 않는 것들 (감성 AI 음악)

실행:
  python orchestrator.py --channel seowon --topic "안전사고 유형 및 대처방법"
  python orchestrator.py --channel jusi   --topic "시니어가 절대 안 알려주는 것들"
  python orchestrator.py --channel unspoken --action benchmark
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# ── 프로젝트 루트 설정 ──────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
WORKSPACE = ROOT / "workspace"
OUTPUT = ROOT / "output"
AGENTS_DIR = ROOT / "agents"

# ── 채널 설정 ────────────────────────────────────────────────────────────────
CHANNEL_CONFIG = {
    "seowon": {
        "name": "서원토건 공식",
        "tone": "전문적·권위있음·신뢰감",
        "tts_voice": "professional_male_kr",
        "resolution": "1920x1080",  # 가로형 (유튜브 롱폼)
        "style": "news_report",
        "color_primary": "#003087",  # 서원토건 CI 블루
        "font": "NanumSquareBold",
        "scene_duration": 7,         # 씬당 평균 초
        "target": "건설 현장 종사자, 안전관리자, 취업 준비생",
    },
    "jusi": {
        "name": "쥬시톡 (JusiTalk)",
        "tone": "친근한 시니어·따뜻함·공감",
        "tts_voice": "warm_male_kr",
        "resolution": "1080x1920",   # 세로형 (쇼츠 우선)
        "style": "casual_talk",
        "color_primary": "#FF6B35",
        "font": "NanumGothic",
        "scene_duration": 6,
        "target": "주니어 직장인, 취업 준비생, 사회초년생",
    },
    "unspoken": {
        "name": "말하지 않는 것들",
        "tone": "감성·무드·여백",
        "tts_voice": None,           # Suno AI 음악 사용
        "resolution": "1080x1920",
        "style": "aesthetic_music",
        "color_primary": "#1A1A2E",
        "font": "NanumMyeongjo",
        "scene_duration": 10,
        "target": "감성적인 음악 팬, 플레이리스트 청취자",
    },
}

# ── 파이프라인 단계 정의 ──────────────────────────────────────────────────────
PIPELINE_STAGES = [
    # Wave 1 - 병렬
    {"id": "scout",       "wave": 1, "agent": "scout_agent",      "parallel": True},
    {"id": "strategist",  "wave": 1, "agent": "strategy_agent",   "parallel": True},
    # Wave 2 - 병렬
    {"id": "researcher",  "wave": 2, "agent": "research_agent",   "parallel": True},
    {"id": "scriptwriter","wave": 2, "agent": "script_agent",     "parallel": True},
    {"id": "visual",      "wave": 2, "agent": "visual_agent",     "parallel": True},
    # Wave 3 - 병렬
    {"id": "tts",         "wave": 3, "agent": "tts_agent",        "parallel": True},
    {"id": "subtitle",    "wave": 3, "agent": "subtitle_agent",   "parallel": True},
    # Wave 4 - 순차
    {"id": "editor",      "wave": 4, "agent": "capcut_builder",   "parallel": False},
    {"id": "qa",          "wave": 4, "agent": "qa_agent",         "parallel": False},
    {"id": "publisher",   "wave": 4, "agent": "youtube_uploader", "parallel": False},
]


class SeowonAutoEngine:
    """메인 오케스트레이터 - 3채널 영상 자동 생성 엔진"""

    def __init__(self, channel: str, topic: str, action: str = "full"):
        if channel not in CHANNEL_CONFIG:
            raise ValueError(f"채널 오류: {channel}. 가능한 채널: {list(CHANNEL_CONFIG.keys())}")

        self.channel = channel
        self.topic = topic
        self.action = action
        self.config = CHANNEL_CONFIG[channel]
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = OUTPUT / f"{channel}_{self.session_id}"
        self.workspace_dir = WORKSPACE / f"{channel}_{self.session_id}"

        # 디렉토리 생성
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        (self.workspace_dir / "scenes").mkdir(exist_ok=True)
        (self.workspace_dir / "audio").mkdir(exist_ok=True)

        # request.md 생성
        self._write_request()

    def _write_request(self):
        """request.md — 파이프라인 진입점"""
        content = f"""# 영상 생성 요청

## 기본 정보
- **채널**: {self.config['name']} ({self.channel})
- **주제**: {self.topic}
- **세션 ID**: {self.session_id}
- **생성일**: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 채널 설정
- **톤**: {self.config['tone']}
- **해상도**: {self.config['resolution']}
- **스타일**: {self.config['style']}
- **주요 색상**: {self.config['color_primary']}
- **씬 길이**: {self.config['scene_duration']}초
- **타겟**: {self.config['target']}

## 작업 경로
- **워크스페이스**: {self.workspace_dir}
- **출력**: {self.session_dir}
"""
        (self.workspace_dir / "request.md").write_text(content, encoding="utf-8")
        print(f"✅ request.md 생성: {self.workspace_dir}/request.md")

    def run(self):
        """전체 파이프라인 실행"""
        print(f"\n{'='*60}")
        print(f"  SEOWON-AUTO ENGINE v1.0")
        print(f"  채널: {self.config['name']}")
        print(f"  주제: {self.topic}")
        print(f"  세션: {self.session_id}")
        print(f"{'='*60}\n")

        if self.action == "benchmark":
            return self._run_benchmark()
        elif self.action == "scout_only":
            return self._run_wave(1)
        elif self.action == "full":
            return self._run_full_pipeline()

    def _run_full_pipeline(self):
        """Wave 1~4 전체 실행"""
        from src.scout_agent import ScoutAgent
        from src.script_agent import ScriptAgent
        from src.tts_agent import TTSAgent
        from src.capcut_builder import CapCutBuilder
        from src.youtube_uploader import YouTubeUploader

        results = {}

        # Wave 1: Scout + Strategist
        print("\n⏳ Wave 1: 레퍼런스 수집 & 전략 수립 (50%)")
        scout = ScoutAgent(self.channel, self.topic, self.workspace_dir)
        results["concept"] = scout.run()
        print(f"  ✅ concept.md 생성")

        # Wave 2: Script + Visual
        print("\n⏳ Wave 2: 대본 & 비주얼 설계 (40%)")
        script = ScriptAgent(self.channel, self.config, self.workspace_dir)
        results["script"] = script.run()
        print(f"  ✅ script.md 생성")

        # Wave 3: TTS + Subtitle
        print("\n⏳ Wave 3: 음성 & 자막 생성 (5%)")
        if self.config["tts_voice"]:
            tts = TTSAgent(self.workspace_dir)
            results["audio"] = tts.run()
            print(f"  ✅ 음성 파일 생성")

        # Wave 4: Edit + QA + Publish
        print("\n⏳ Wave 4: 편집 & 검수 & 업로드 (5%)")
        builder = CapCutBuilder(self.channel, self.workspace_dir, self.session_dir)
        results["capcut"] = builder.run()
        print(f"  ✅ CapCut 프로젝트 생성")

        print(f"\n{'='*60}")
        print(f"  ✅ 완료! 세션: {self.session_id}")
        print(f"  📁 출력: {self.session_dir}")
        print(f"{'='*60}\n")

        return results

    def _run_benchmark(self):
        """unspoken 채널 전용: 10만+ 채널 벤치마킹"""
        from src.scout_agent import ScoutAgent
        scout = ScoutAgent(self.channel, "10만+ 감성 음악 플레이리스트", self.workspace_dir)
        return scout.run_benchmark()

    def _run_wave(self, wave_num: int):
        """특정 Wave만 실행"""
        stages = [s for s in PIPELINE_STAGES if s["wave"] == wave_num]
        print(f"\n⏳ Wave {wave_num} 실행: {[s['id'] for s in stages]}")


def main():
    parser = argparse.ArgumentParser(description="SEOWON-AUTO ENGINE v1.0")
    parser.add_argument("--channel", required=True,
                        choices=["seowon", "jusi", "unspoken"],
                        help="채널 선택")
    parser.add_argument("--topic", default="",
                        help="영상 주제")
    parser.add_argument("--action", default="full",
                        choices=["full", "scout_only", "benchmark"],
                        help="실행 모드")
    args = parser.parse_args()

    engine = SeowonAutoEngine(
        channel=args.channel,
        topic=args.topic,
        action=args.action,
    )
    engine.run()


if __name__ == "__main__":
    main()
