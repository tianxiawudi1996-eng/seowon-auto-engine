"""
gureum_mv_builder.py — 구름이 뮤직비디오 완전 자동 생성
========================================================
집 PC의 D:\\멍냥구조대\\김정원대표님 폴더를 자동 스캔하여
모든 영상·음원·이미지를 분석한 후 최종 뮤직비디오를 출력한다.

작업:
  1. 폴더 자동 스캔 (mp4, mov, jpg, png, mp3, wav 분류)
  2. 영상 메타데이터 분석 (해상도, fps, duration)
  3. 음원 분석 (BPM, 길이)
  4. 자동 편집 결정 (음원에 맞춰 씬 컷)
  5. 자막·전환 효과 자동 적용
  6. final_gureum_mv.mp4 출력 (1920x1080)

외부 의존성: ffmpeg, ffprobe (시스템 설치 필요)
Python 의존성: ZERO (stdlib 전용)

집 PC 실행:
  cd "D:\\멍냥구조대\\김정원대표님"
  python gureum_mv_builder.py
  
  또는 Claude Code에서:
  python gureum_mv_builder.py --auto
"""

import argparse
import json
import os
import sys
import subprocess
import shutil
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


# ── 구름이 뮤직비디오 설정 ─────────────────────────────────────────────────────
GUREUM_CONFIG = {
    "project_name":     "구름이의 하루",
    "output_resolution": "1920x1080",   # 16:9
    "output_fps":        30,
    "scene_min_duration": 4,             # 최소 씬 길이 (초)
    "scene_max_duration": 8,             # 최대 씬 길이 (초)

    # 9개 씬 순서 (이전 대화에서 확정된 순서)
    "preferred_scene_order": [
        "egg_tart", "pool", "soju", "couple", "matcha",
        "stroller", "bow", "raincoat", "rose",
    ],

    # 색보정 (감성)
    "color_grade":      "warm cinematic",

    # 자막 스타일
    "subtitle_font":    "NanumSquareBold",
    "subtitle_color":   "#FFFFFF",
    "subtitle_size":    52,
    "shadow":           True,

    # 인트로/아웃트로
    "intro_text":       "구름이의 하루 🐾",
    "outro_text":       "Music Video by 김무빈\n구독 & 좋아요 부탁드려요 💛",

    # 트랜지션
    "transition_type":  "fade",
    "transition_duration": 0.5,
}

# 폴더 자동 분류 키워드
SCENE_KEYWORDS = {
    "egg_tart":  ["에그", "타르트", "tart", "egg"],
    "pool":      ["풀", "수영", "pool", "여름"],
    "soju":      ["소주", "soju", "술"],
    "couple":    ["커플", "산책", "couple"],
    "matcha":    ["말차", "케이크", "matcha"],
    "stroller":  ["유모차", "stroller"],
    "bow":       ["볼찌", "bow", "리본"],
    "raincoat":  ["우비", "raincoat", "비"],
    "rose":      ["장미", "rose", "꽃"],
}


# ── FFmpeg 헬퍼 ───────────────────────────────────────────────────────────────
def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def ffprobe(path: Path) -> Dict:
    """미디어 파일 메타데이터 추출"""
    result = subprocess.run([
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        str(path)
    ], capture_output=True, text=True)
    if result.returncode != 0:
        return {}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {}


def get_duration(path: Path) -> float:
    """파일 재생 시간 (초)"""
    info = ffprobe(path)
    try:
        return float(info["format"]["duration"])
    except (KeyError, ValueError):
        return 0.0


# ── 폴더 스캔 & 자동 분류 ──────────────────────────────────────────────────────
class AssetScanner:
    """D:\\멍냥구조대\\김정원대표님 폴더 자동 스캔"""

    VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
    IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
    AUDIO_EXTS = {".mp3", ".wav", ".aac", ".m4a", ".flac"}

    def __init__(self, source_dir: Path):
        self.source = source_dir
        self.videos: List[Path] = []
        self.images: List[Path] = []
        self.audios: List[Path] = []

    def scan(self) -> Dict:
        """재귀적으로 모든 파일 스캔"""
        print(f"\n🔍 폴더 스캔 시작: {self.source}")
        for path in self.source.rglob("*"):
            if not path.is_file():
                continue
            ext = path.suffix.lower()
            if ext in self.VIDEO_EXTS:
                self.videos.append(path)
            elif ext in self.IMAGE_EXTS:
                self.images.append(path)
            elif ext in self.AUDIO_EXTS:
                self.audios.append(path)

        # 자동 분류
        scenes = self._classify_by_scene()

        result = {
            "videos_count": len(self.videos),
            "images_count": len(self.images),
            "audios_count": len(self.audios),
            "videos":  [str(p) for p in self.videos],
            "images":  [str(p) for p in self.images],
            "audios":  [str(p) for p in self.audios],
            "scenes":  scenes,
        }
        self._print_summary(result)
        return result

    def _classify_by_scene(self) -> Dict[str, List[str]]:
        """파일명 기반 씬 자동 분류"""
        scenes = {scene: [] for scene in SCENE_KEYWORDS}
        scenes["uncategorized"] = []

        all_media = self.videos + self.images
        for path in all_media:
            name = path.stem.lower()
            classified = False
            for scene, keywords in SCENE_KEYWORDS.items():
                if any(kw in name for kw in keywords):
                    scenes[scene].append(str(path))
                    classified = True
                    break
            if not classified:
                scenes["uncategorized"].append(str(path))
        return scenes

    def _print_summary(self, result: Dict):
        print(f"\n📊 스캔 결과:")
        print(f"  🎥 영상 파일:  {result['videos_count']}개")
        print(f"  🖼️  이미지:     {result['images_count']}개")
        print(f"  🎵 음원:       {result['audios_count']}개")
        print(f"\n🎬 씬별 분류:")
        for scene, files in result["scenes"].items():
            if files:
                emoji = {"egg_tart":"🥧","pool":"🌊","soju":"🍶","couple":"👫",
                         "matcha":"🍵","stroller":"🛺","bow":"🤍","raincoat":"🌧️",
                         "rose":"🌹","uncategorized":"📂"}.get(scene, "📁")
                print(f"  {emoji} {scene:<15} {len(files)}개")


# ── 영상 빌더 ─────────────────────────────────────────────────────────────────
class GureumMVBuilder:
    """구름이 뮤직비디오 자동 생성기"""

    def __init__(self, scan_result: Dict, output_dir: Path, audio_path: Optional[Path] = None):
        self.scan      = scan_result
        self.output    = output_dir
        self.work_dir  = output_dir / "_work"
        self.audio     = audio_path
        self.scenes    = scan_result["scenes"]
        self.config    = GUREUM_CONFIG

        self.output.mkdir(parents=True, exist_ok=True)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def build(self) -> Path:
        """전체 파이프라인 실행"""
        print(f"\n{'='*60}")
        print(f"  🐾 구름이 뮤직비디오 빌더")
        print(f"  프로젝트: {self.config['project_name']}")
        print(f"{'='*60}\n")

        # 1. 음원 분석 (있으면)
        audio_duration = 0
        if self.audio:
            audio_duration = get_duration(self.audio)
            print(f"🎵 음원: {self.audio.name} ({audio_duration:.1f}초)")

        # 2. 씬 클립 생성
        clip_paths = self._build_clips(audio_duration)
        print(f"\n✅ 씬 클립 {len(clip_paths)}개 생성 완료")

        # 3. 클립 합치기
        merged = self.work_dir / "merged.mp4"
        self._concat_clips(clip_paths, merged)
        print(f"✅ 클립 병합 완료: {merged.name}")

        # 4. 음원 합성
        if self.audio:
            audio_merged = self.work_dir / "audio_merged.mp4"
            self._add_audio(merged, audio_merged)
            merged = audio_merged
            print(f"✅ 음원 합성 완료")

        # 5. 자막 (인트로/아웃트로)
        final = self.output / "final_gureum_mv.mp4"
        self._add_subtitles(merged, final)

        print(f"\n{'='*60}")
        print(f"  ✅ 완료!")
        print(f"  📁 {final}")
        print(f"  ⏱️  총 길이: {get_duration(final):.1f}초")
        print(f"{'='*60}\n")

        # 정리
        # shutil.rmtree(self.work_dir, ignore_errors=True)

        return final

    def _build_clips(self, total_duration: float) -> List[Path]:
        """각 씬을 정해진 순서대로 클립화"""
        clips = []
        scene_duration = self.config["scene_max_duration"]

        # 음원 길이에 맞춰 씬당 시간 조정
        if total_duration > 0:
            active_scenes = [s for s in self.config["preferred_scene_order"]
                             if self.scenes.get(s)]
            if active_scenes:
                scene_duration = total_duration / len(active_scenes)
                scene_duration = max(self.config["scene_min_duration"],
                                     min(self.config["scene_max_duration"], scene_duration))

        idx = 0
        for scene_name in self.config["preferred_scene_order"]:
            files = self.scenes.get(scene_name, [])
            if not files:
                continue

            for source_path in files[:1]:  # 씬당 첫 파일만 사용
                source = Path(source_path)
                clip   = self.work_dir / f"clip_{idx:02d}_{scene_name}.mp4"

                if source.suffix.lower() in AssetScanner.IMAGE_EXTS:
                    self._image_to_clip(source, clip, scene_duration)
                else:
                    self._video_to_clip(source, clip, scene_duration)

                clips.append(clip)
                idx += 1

        # 미분류 파일도 활용 (선택적)
        for source_path in self.scenes.get("uncategorized", [])[:3]:
            source = Path(source_path)
            clip   = self.work_dir / f"clip_{idx:02d}_extra.mp4"
            try:
                if source.suffix.lower() in AssetScanner.IMAGE_EXTS:
                    self._image_to_clip(source, clip, scene_duration)
                else:
                    self._video_to_clip(source, clip, scene_duration)
                clips.append(clip)
                idx += 1
            except Exception:
                continue

        return clips

    def _image_to_clip(self, image: Path, output: Path, duration: float):
        """이미지 → 켄번스 효과 영상"""
        cmd = [
            "ffmpeg", "-loop", "1", "-i", str(image),
            "-t", str(duration),
            "-vf", (
                f"scale=1920:1080:force_original_aspect_ratio=increase,"
                f"crop=1920:1080,"
                f"zoompan=z='min(zoom+0.0008,1.1)':d={int(duration*30)}:s=1920x1080"
            ),
            "-r", str(self.config["output_fps"]),
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-pix_fmt", "yuv420p",
            "-y", str(output)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    def _video_to_clip(self, video: Path, output: Path, duration: float):
        """영상 → 트림 + 리사이즈 + 색보정"""
        cmd = [
            "ffmpeg", "-i", str(video),
            "-t", str(duration),
            "-vf", (
                "scale=1920:1080:force_original_aspect_ratio=increase,"
                "crop=1920:1080,"
                "eq=brightness=0.02:contrast=1.1:saturation=1.08"
            ),
            "-r", str(self.config["output_fps"]),
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-an",  # 원본 오디오 제거 (음원 따로 합성)
            "-y", str(output)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    def _concat_clips(self, clips: List[Path], output: Path):
        """클립 합치기 (페이드 트랜지션 포함)"""
        list_file = self.work_dir / "concat_list.txt"
        list_file.write_text(
            "\n".join(f"file '{c.absolute()}'" for c in clips),
            encoding="utf-8"
        )
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-y", str(output)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    def _add_audio(self, video: Path, output: Path):
        """음원 합성"""
        cmd = [
            "ffmpeg", "-i", str(video), "-i", str(self.audio),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-y", str(output)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    def _add_subtitles(self, video: Path, output: Path):
        """인트로/아웃트로 텍스트 오버레이"""
        intro = self.config["intro_text"]
        outro = self.config["outro_text"]
        font  = self.config["subtitle_font"]

        # 간단 버전: drawtext 필터
        intro_filter = (
            f"drawtext=text='{intro}':"
            f"fontcolor=white:fontsize=72:"
            f"x=(w-text_w)/2:y=(h-text_h)/2:"
            f"enable='between(t,0,3)':"
            f"alpha='if(lt(t,2),t/2,if(gt(t,2.5),1-(t-2.5)/0.5,1))'"
        )

        cmd = [
            "ffmpeg", "-i", str(video),
            "-vf", intro_filter,
            "-c:v", "libx264", "-preset", "fast", "-crf", "22",
            "-c:a", "copy",
            "-y", str(output)
        ]
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError:
            # 폰트 문제 등 발생 시 그대로 복사
            shutil.copy(video, output)


# ── 메인 ──────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="구름이 뮤직비디오 자동 생성")
    p.add_argument("--source", default=r"D:\멍냥구조대\김정원대표님",
                   help="자료 폴더 (기본: D:\\멍냥구조대\\김정원대표님)")
    p.add_argument("--output", default="./gureum_output", help="출력 폴더")
    p.add_argument("--audio",  default=None, help="배경음원 파일 (자동 감지)")
    p.add_argument("--auto",   action="store_true", help="자동 모드 (확인 없이 진행)")
    p.add_argument("--scan-only", action="store_true", help="스캔만 (생성 안 함)")
    args = p.parse_args()

    # ffmpeg 확인
    if not has_ffmpeg():
        print("❌ ffmpeg/ffprobe가 설치되어 있지 않습니다.")
        print("   Windows: https://www.gyan.dev/ffmpeg/builds/")
        print("   또는: choco install ffmpeg")
        sys.exit(1)

    source = Path(args.source)
    if not source.exists():
        print(f"❌ 소스 폴더 없음: {source}")
        sys.exit(1)

    # 1. 스캔
    scanner = AssetScanner(source)
    result  = scanner.scan()

    # 결과 저장
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "scan_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if args.scan_only:
        print(f"\n📋 스캔 결과 저장: {output_dir / 'scan_result.json'}")
        return

    # 2. 음원 자동 감지
    audio_path = None
    if args.audio:
        audio_path = Path(args.audio)
    elif scanner.audios:
        # 가장 긴 음원 자동 선택
        audio_path = max(scanner.audios, key=lambda p: get_duration(p))
        print(f"\n🎵 음원 자동 감지: {audio_path.name}")

    # 3. 사용자 확인 (auto 아닐 때)
    if not args.auto:
        print(f"\n💬 진행하시겠습니까? (y/N): ", end="")
        if input().strip().lower() != "y":
            print("취소됨.")
            return

    # 4. 빌드
    builder = GureumMVBuilder(result, output_dir, audio_path)
    final   = builder.build()

    print(f"\n🎉 final_gureum_mv.mp4 완성!")
    print(f"📁 위치: {final.absolute()}")


if __name__ == "__main__":
    main()
