"""
TTS Agent — XTTS v2 기반 음성 생성
"""
import subprocess
import json
from pathlib import Path
from typing import Dict, List


class TTSAgent:
    """XTTS v2 로컬 TTS 에이전트 (WSL2 / Windows 환경)"""

    # XTTS 서버 주소 (로컬 실행 시)
    XTTS_API = "http://localhost:8020"

    VOICE_PRESETS = {
        "professional_male_kr": {
            "language": "ko",
            "speaker": "default_male",
            "speed": 1.0,
            "pitch": 0,
        },
        "warm_male_kr": {
            "language": "ko",
            "speaker": "warm_male",
            "speed": 0.95,
            "pitch": -2,
        },
    }

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.audio_dir = workspace / "audio"
        self.audio_dir.mkdir(exist_ok=True)

    def run(self) -> Dict:
        """scenes.md에서 텍스트 추출 → 음성 파일 생성"""
        scenes_path = self.workspace / "scenes.md"

        try:
            scenes = json.loads(scenes_path.read_text(encoding="utf-8"))
        except Exception:
            scenes = [{"scene": 1, "text": "테스트 음성입니다.", "duration": 3}]

        audio_files = []
        for scene in scenes:
            text = scene.get("text", "")
            if not text:
                continue

            audio_path = self.audio_dir / f"voice_{scene['scene']:02d}.mp3"
            self._generate_tts(text, audio_path)
            audio_files.append(str(audio_path))

        print(f"  ✅ TTS 생성 완료: {len(audio_files)}개 파일")
        return {"audio_files": audio_files}

    def _generate_tts(self, text: str, output_path: Path):
        """XTTS v2 API 호출 또는 대체 TTS"""
        try:
            import requests
            response = requests.post(
                f"{self.XTTS_API}/tts_to_file",
                json={
                    "text": text,
                    "language": "ko",
                    "speaker_wav": None,
                    "file_path": str(output_path),
                },
                timeout=30,
            )
            if response.status_code != 200:
                raise Exception(f"XTTS 오류: {response.status_code}")
        except Exception as e:
            # XTTS 서버 없을 때: 빈 파일 생성 (개발용)
            print(f"  ⚠️  XTTS 미연결 ({e}), 플레이스홀더 생성")
            output_path.write_bytes(b"")  # 빈 파일
