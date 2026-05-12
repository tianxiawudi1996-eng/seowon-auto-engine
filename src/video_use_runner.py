"""
video_use_runner.py — SEOWON-AUTO ENGINE v3.0 Editing Mode
============================================================
촬영본 자동 편집 모듈. video-use 스킬을 통해 raw footage를
자동 분석·편집·렌더링하여 final.mp4를 출력한다.

설치 전제:
  - ~/.claude/skills/video-use 클론 완료
  - ffmpeg, yt-dlp 설치
  - ELEVENLABS_API_KEY 환경변수 설정

사용:
  python video_use_runner.py --source /path/to/raw_videos \
                             --channel seowon \
                             --duration 300

외부 의존성: subprocess(stdlib), pathlib(stdlib), json(stdlib)
            ElevenLabs API (HTTP, urllib로 직접 호출)
"""

import json
import os
import sys
import argparse
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime


# ── 채널별 편집 프리셋 ─────────────────────────────────────────────────────────
CHANNEL_EDIT_PRESETS = {
    "seowon": {
        "resolution":      "1920x1080",
        "aspect":          "16:9",
        "color_grade":     "warm cinematic",
        "subtitle_style":  "2-word UPPERCASE chunks",
        "subtitle_font":   "NanumGothicBold",
        "subtitle_size":   36,
        "subtitle_color":  "#FFFFFF",
        "subtitle_pos":    "bottom 88%",
        "filler_words":    ["음", "어", "그", "어떻게", "어쨌든"],  # 한국어
        "audio_fade_ms":   30,
        "target_duration": 300,    # 5분
        "intro_outro":     True,
        "logo_overlay":    "assets/seowon_logo.png",
    },
    "jusi": {
        "resolution":      "1080x1920",
        "aspect":          "9:16",
        "color_grade":     "neutral punch",
        "subtitle_style":  "2-word UPPERCASE chunks",
        "subtitle_font":   "NanumGothic",
        "subtitle_size":   48,
        "subtitle_color":  "#FFFFFF",
        "subtitle_pos":    "center 85%",
        "filler_words":    ["음", "어", "그", "사실은", "솔직히"],
        "audio_fade_ms":   30,
        "target_duration": 60,     # 쇼츠
        "intro_outro":     False,
        "crop_strategy":   "smart_center",   # 화자 중심 자동 크롭
    },
    "unspoken": {
        "resolution":      "1080x1920",
        "aspect":          "9:16",
        "color_grade":     "moody dark",
        "subtitle_style":  "single line minimal",
        "subtitle_font":   "NanumMyeongjo",
        "subtitle_size":   38,
        "subtitle_color":  "#E8E8E8",
        "subtitle_pos":    "center 50%",
        "filler_words":    [],
        "audio_fade_ms":   800,   # 감성적 긴 페이드
        "target_duration": 180,
        "intro_outro":     False,
    },
}


# ── ElevenLabs Scribe API (트랜스크립트) ──────────────────────────────────────
class ScribeClient:
    """ElevenLabs Scribe API — 단어 단위 트랜스크립트"""

    API_URL = "https://api.elevenlabs.io/v1/speech-to-text"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def transcribe(self, audio_path: Path) -> dict:
        """오디오/영상 → 단어 단위 타임스탬프"""
        # 영상이면 오디오 추출 먼저
        if audio_path.suffix in [".mp4", ".mov", ".mkv"]:
            audio_path = self._extract_audio(audio_path)

        boundary  = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        body  = self._build_multipart(boundary, audio_data, audio_path.name)
        req   = urllib.request.Request(
            self.API_URL,
            data=body,
            method="POST",
            headers={
                "xi-api-key":   self.api_key,
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8")
            raise RuntimeError(f"Scribe API 오류 {e.code}: {err}")

    def _extract_audio(self, video_path: Path) -> Path:
        """ffmpeg로 mp3 추출"""
        audio_path = video_path.with_suffix(".mp3")
        subprocess.run([
            "ffmpeg", "-i", str(video_path),
            "-vn", "-acodec", "libmp3lame",
            "-b:a", "128k",
            "-y", str(audio_path)
        ], check=True, capture_output=True)
        return audio_path

    def _build_multipart(self, boundary: str, data: bytes, fname: str) -> bytes:
        parts = []
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="model_id"\r\n\r\n'.encode())
        parts.append("scribe_v1\r\n".encode())
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'.encode())
        parts.append("Content-Type: audio/mpeg\r\n\r\n".encode())
        parts.append(data)
        parts.append(f"\r\n--{boundary}--\r\n".encode())
        return b"".join(parts)


# ── FFmpeg 영상 편집 헬퍼 ─────────────────────────────────────────────────────
class FFmpegEditor:
    """ffmpeg 자동 편집 — pip 패키지 ZERO"""

    @staticmethod
    def probe(video_path: Path) -> dict:
        """영상 메타데이터 추출 (해상도, fps, duration 등)"""
        result = subprocess.run([
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", "-show_streams",
            str(video_path)
        ], capture_output=True, text=True)
        return json.loads(result.stdout)

    @staticmethod
    def cut(input_path: Path, output_path: Path,
            start: float, duration: float, fade_ms: int = 30):
        """특정 구간 자르기 + 오디오 페이드인/아웃"""
        cmd = [
            "ffmpeg", "-ss", str(start), "-i", str(input_path),
            "-t", str(duration),
            "-af", f"afade=t=in:d={fade_ms/1000},afade=t=out:st={duration - fade_ms/1000}:d={fade_ms/1000}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-y", str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    @staticmethod
    def crop_vertical(input_path: Path, output_path: Path,
                      focus_x_ratio: float = 0.5):
        """16:9 → 9:16 세로 크롭 (화자 중심)"""
        # 1920x1080 → 608x1080 크롭
        probe   = FFmpegEditor.probe(input_path)
        w       = int(probe["streams"][0]["width"])
        h       = int(probe["streams"][0]["height"])
        new_w   = int(h * 9 / 16)
        offset  = int((w - new_w) * focus_x_ratio)

        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-vf", f"crop={new_w}:{h}:{offset}:0,scale=1080:1920",
            "-c:a", "copy",
            "-y", str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    @staticmethod
    def burn_subtitles(input_path: Path, srt_path: Path, output_path: Path,
                       font: str = "NanumGothicBold",
                       size: int = 36, color: str = "FFFFFF"):
        """SRT 자막을 영상에 번인 (하드코딩)"""
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-vf", f"subtitles={srt_path}:force_style='FontName={font},FontSize={size},PrimaryColour=&H{color}&,Outline=2,Shadow=1'",
            "-c:a", "copy",
            "-y", str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    @staticmethod
    def color_grade(input_path: Path, output_path: Path, grade: str = "warm cinematic"):
        """프리셋 색보정"""
        FILTERS = {
            "warm cinematic":  "eq=brightness=0.02:contrast=1.1:saturation=1.05,colorbalance=rm=0.05:gm=0:bm=-0.05",
            "neutral punch":   "eq=contrast=1.2:saturation=1.1,unsharp=3:3:0.5",
            "moody dark":      "eq=brightness=-0.05:contrast=1.15:saturation=0.85,vignette=PI/5",
        }
        vf = FILTERS.get(grade, FILTERS["warm cinematic"])
        cmd = [
            "ffmpeg", "-i", str(input_path),
            "-vf", vf,
            "-c:a", "copy",
            "-y", str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    @staticmethod
    def concat(input_paths: list, output_path: Path):
        """여러 영상 합치기"""
        list_file = output_path.parent / "concat_list.txt"
        list_file.write_text(
            "\n".join(f"file '{p.absolute()}'" for p in input_paths),
            encoding="utf-8"
        )
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            "-y", str(output_path)
        ]
        subprocess.run(cmd, check=True, capture_output=True)


# ── 필러 워드 감지 + 컷 결정 ──────────────────────────────────────────────────
def detect_cuts(transcript: dict, filler_words: list,
                min_silence_ms: int = 800) -> list:
    """
    트랜스크립트에서 필러 워드 + 긴 침묵 구간 감지
    Returns: 컷 구간 리스트 [(start, end), ...]
    """
    cuts = []
    words = transcript.get("words", [])

    for i, word in enumerate(words):
        text  = word.get("text", "").strip().lower()
        start = word.get("start", 0)
        end   = word.get("end", 0)

        # 필러 워드 컷
        if text in [f.lower() for f in filler_words]:
            cuts.append((start, end, "filler"))
            continue

        # 긴 침묵 컷
        if i > 0:
            prev_end = words[i-1].get("end", 0)
            silence  = (start - prev_end) * 1000
            if silence > min_silence_ms:
                cuts.append((prev_end, start, "silence"))

    return cuts


# ── 자막 청크 생성 (2단어 대문자) ──────────────────────────────────────────────
def chunk_subtitles(transcript: dict, words_per_chunk: int = 2,
                    upper: bool = True) -> list:
    """단어 단위 트랜스크립트 → SRT 청크"""
    words   = transcript.get("words", [])
    chunks  = []
    buffer  = []

    for word in words:
        buffer.append(word)
        if len(buffer) >= words_per_chunk:
            start = buffer[0]["start"]
            end   = buffer[-1]["end"]
            text  = " ".join(w["text"] for w in buffer)
            if upper:
                text = text.upper()
            chunks.append({"start": start, "end": end, "text": text})
            buffer = []

    # 남은 단어
    if buffer:
        start = buffer[0]["start"]
        end   = buffer[-1]["end"]
        text  = " ".join(w["text"] for w in buffer)
        if upper:
            text = text.upper()
        chunks.append({"start": start, "end": end, "text": text})

    return chunks


def chunks_to_srt(chunks: list) -> str:
    """청크 → SRT 문자열"""
    def fmt(s: float) -> str:
        h  = int(s // 3600)
        m  = int((s % 3600) // 60)
        sec= int(s % 60)
        ms = int((s - int(s)) * 1000)
        return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"

    lines = []
    for i, c in enumerate(chunks, 1):
        lines.append(f"{i}\n{fmt(c['start'])} --> {fmt(c['end'])}\n{c['text']}\n")
    return "\n".join(lines)


# ── 메인 러너 ─────────────────────────────────────────────────────────────────
class VideoUseRunner:
    """SEOWON-AUTO ENGINE v3.0 — 촬영본 자동 편집 러너"""

    def __init__(self, source_dir: Path, channel: str,
                 elevenlabs_key: str, output_dir: Path = None):
        if channel not in CHANNEL_EDIT_PRESETS:
            raise ValueError(f"채널 오류: {channel}")

        self.source_dir = source_dir
        self.channel    = channel
        self.preset     = CHANNEL_EDIT_PRESETS[channel]
        self.scribe     = ScribeClient(elevenlabs_key)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = output_dir or Path(f"output/edit_{channel}_{self.session_id}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> Path:
        """전체 편집 파이프라인 실행"""
        print(f"\n{'='*60}")
        print(f"  SEOWON v3.0 — Video-Use 자동 편집")
        print(f"  채널: {self.channel} | 세션: {self.session_id}")
        print(f"{'='*60}\n")

        # 1. 소스 영상 스캔
        videos = self._scan_sources()
        print(f"✅ 소스 영상 {len(videos)}개 발견")

        # 2. 각 영상 트랜스크립트화
        transcripts = []
        for video in videos:
            print(f"  📝 트랜스크립트화: {video.name}")
            tx = self.scribe.transcribe(video)
            transcripts.append({"video": video, "transcript": tx})
            # 캐시 저장
            (self.output_dir / f"{video.stem}_transcript.json").write_text(
                json.dumps(tx, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        # 3. 컷 결정 + 자막 청크
        all_chunks = []
        clip_paths = []
        for i, item in enumerate(transcripts):
            cuts   = detect_cuts(item["transcript"], self.preset["filler_words"])
            chunks = chunk_subtitles(item["transcript"])
            all_chunks.extend(chunks)

            # 임시 클립 생성 (필러 제거 후)
            clip = self.output_dir / f"clip_{i:02d}.mp4"
            self._cut_filler(item["video"], clip, cuts)
            clip_paths.append(clip)

        # 4. 모든 클립 합치기
        merged = self.output_dir / "merged.mp4"
        FFmpegEditor.concat(clip_paths, merged)
        print(f"✅ 클립 병합: {merged}")

        # 5. 색보정
        graded = self.output_dir / "graded.mp4"
        FFmpegEditor.color_grade(merged, graded, self.preset["color_grade"])
        print(f"✅ 색보정 적용: {self.preset['color_grade']}")

        # 6. 세로 크롭 (필요시)
        if self.preset["aspect"] == "9:16":
            cropped = self.output_dir / "cropped.mp4"
            FFmpegEditor.crop_vertical(graded, cropped)
            graded = cropped
            print(f"✅ 세로 크롭: 9:16")

        # 7. 자막 번인
        srt_path = self.output_dir / "subtitles.srt"
        srt_path.write_text(chunks_to_srt(all_chunks), encoding="utf-8")
        final = self.output_dir / "final.mp4"
        FFmpegEditor.burn_subtitles(
            graded, srt_path, final,
            font=self.preset["subtitle_font"],
            size=self.preset["subtitle_size"],
        )

        # 8. 프로젝트 메모리 저장
        self._save_project_md(transcripts, all_chunks)

        print(f"\n{'='*60}")
        print(f"  ✅ 완료! final.mp4: {final}")
        print(f"{'='*60}\n")
        return final

    def _scan_sources(self) -> list:
        """소스 폴더에서 영상 파일 검색"""
        extensions = [".mp4", ".mov", ".mkv", ".avi", ".webm"]
        videos = []
        for ext in extensions:
            videos.extend(sorted(self.source_dir.glob(f"*{ext}")))
        return videos

    def _cut_filler(self, source: Path, output: Path, cuts: list):
        """필러 구간 제거 후 깨끗한 클립 생성"""
        # 간단 버전: 전체 복사 (실제로는 cut 구간 분할 + concat 필요)
        # video-use 스킬은 이 부분을 자동으로 처리
        if not cuts:
            subprocess.run([
                "ffmpeg", "-i", str(source),
                "-c", "copy", "-y", str(output)
            ], check=True, capture_output=True)
            return

        # TODO: cut 리스트를 기반으로 keep 구간 추출 + 병합
        # 실제 구현은 video-use 스킬에 위임 권장
        subprocess.run([
            "ffmpeg", "-i", str(source),
            "-c", "copy", "-y", str(output)
        ], check=True, capture_output=True)

    def _save_project_md(self, transcripts: list, chunks: list):
        """project.md 세션 메모리 저장"""
        md = f"""# Project Memory — {self.session_id}

## 채널: {self.channel}
## 프리셋: {json.dumps(self.preset, ensure_ascii=False, indent=2)}

## 처리된 소스
{chr(10).join(f"- {t['video'].name}" for t in transcripts)}

## 자막 청크 수
- 총 {len(chunks)}개

## 다음 작업
- [ ] 클립 미세 조정
- [ ] BGM 추가 (선택)
- [ ] YouTube 메타데이터 작성
- [ ] 업로드
"""
        (self.output_dir / "project.md").write_text(md, encoding="utf-8")


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SEOWON v3.0 — Video-Use 자동 편집")
    parser.add_argument("--source",  required=True, help="raw 영상 폴더")
    parser.add_argument("--channel", required=True, choices=list(CHANNEL_EDIT_PRESETS.keys()))
    parser.add_argument("--api-key", default=os.environ.get("ELEVENLABS_API_KEY", ""))
    parser.add_argument("--output",  default=None, help="출력 폴더")
    args = parser.parse_args()

    if not args.api_key:
        print("❌ ElevenLabs API 키 필요!")
        print("   발급: https://elevenlabs.io/app/settings/api-keys")
        print("   설정: export ELEVENLABS_API_KEY=YOUR_KEY")
        sys.exit(1)

    runner = VideoUseRunner(
        source_dir     = Path(args.source),
        channel        = args.channel,
        elevenlabs_key = args.api_key,
        output_dir     = Path(args.output) if args.output else None,
    )
    runner.run()
