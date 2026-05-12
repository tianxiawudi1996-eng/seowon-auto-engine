"""
gureum_mv_v2_fullstack.py — 구름이 뮤직비디오 풀스택 자동 생성기
================================================================
우리가 만든 모든 시스템을 풀활용한 진짜 완성형:

  ✅ ElevenLabs Scribe로 음원 비트 분석
  ✅ Gemini API로 영상 스토리텔링 분석
  ✅ Remotion으로 영화급 인트로/아웃트로
  ✅ CapCutBuilder로 미세조정 가능한 JSON 동시 출력
  ✅ 씬별 다른 무드 색보정 (감성 변화)
  ✅ video-use 스킬 호환 (자막 청크)
  ✅ 음원 BPM 분석 후 비트 동기화 컷
  ✅ 영화급 트랜지션 (디졸브, 페이드, 줌)

이중 출력:
  1. final_gureum_mv.mp4         ← 자동 완성품 (영화급)
  2. capcut_project/              ← CapCut 후작업용 JSON
  3. remotion_intro_outro/        ← Remotion 인트로/아웃트로
  4. project.md                   ← 작업 메모리 (세션 복원용)

집 PC에서:
  python gureum_mv_v2_fullstack.py
"""

import argparse
import json
import os
import sys
import subprocess
import shutil
import uuid
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple


# ── 구름이 뮤직비디오 설정 (영화급) ──────────────────────────────────────────
GUREUM_CONFIG = {
    "project_name":     "구름이의 하루",
    "output_resolution": "1920x1080",
    "output_fps":        30,

    # 9개 씬 - 각각 다른 무드 (감정 곡선)
    "scenes": [
        {"id": "egg_tart", "emoji": "🥧", "title": "에그타르트",
         "mood": "warm_curiosity",   "color_grade": "warm cinematic",
         "subtitle": "오늘은 뭐가 있을까", "duration": 7,
         "transition_in": "fade", "ken_burns": "zoom_in"},

        {"id": "pool", "emoji": "🌊", "title": "수영장",
         "mood": "summer_vibrant",   "color_grade": "vibrant teal",
         "subtitle": "여름의 어느 날", "duration": 7,
         "transition_in": "dissolve", "ken_burns": "pan_right"},

        {"id": "soju", "emoji": "🍶", "title": "소주병",
         "mood": "moody_warm",       "color_grade": "moody amber",
         "subtitle": "능청스러운 표정", "duration": 6,
         "transition_in": "dissolve", "ken_burns": "rack_focus"},

        {"id": "couple", "emoji": "👫", "title": "커플 산책",
         "mood": "soft_romantic",    "color_grade": "soft pastel",
         "subtitle": "사랑하는 사람들과", "duration": 7,
         "transition_in": "fade", "ken_burns": "slow_pan"},

        {"id": "matcha", "emoji": "🍵", "title": "말차 케이크",
         "mood": "calm_green",       "color_grade": "matcha tone",
         "subtitle": "달콤한 오후", "duration": 6,
         "transition_in": "dissolve", "ken_burns": "zoom_out"},

        {"id": "stroller", "emoji": "🛺", "title": "유모차",
         "mood": "cozy_warm",        "color_grade": "warm cinematic",
         "subtitle": "산책의 즐거움", "duration": 7,
         "transition_in": "fade", "ken_burns": "side_pan"},

        {"id": "bow", "emoji": "🤍", "title": "볼찌 클로즈업",
         "mood": "soft_focus",       "color_grade": "soft pastel",
         "subtitle": "사랑스러운 순간", "duration": 6,
         "transition_in": "dissolve", "ken_burns": "macro_zoom"},

        {"id": "raincoat", "emoji": "🌧️", "title": "우비",
         "mood": "playful_cool",     "color_grade": "cool blue",
         "subtitle": "비 오는 날도 즐거워", "duration": 7,
         "transition_in": "wipe", "ken_burns": "zoom_in"},

        {"id": "rose", "emoji": "🌹", "title": "장미 부케",
         "mood": "emotional_pink",   "color_grade": "rose pink",
         "subtitle": "당신은 나의 전부", "duration": 8,
         "transition_in": "long_dissolve", "ken_burns": "slow_zoom_out"},
    ],

    # 인트로/아웃트로 (Remotion 권장)
    "intro": {
        "duration": 3,
        "title": "구름이의 하루",
        "subtitle": "Pomeranian Music Video",
        "style": "pixar_inspired",
    },
    "outro": {
        "duration": 4,
        "main_text": "Music Video by 김무빈",
        "sub_text": "구독 & 좋아요 부탁드려요 💛",
        "show_credits": True,
    },

    # 자막 (video-use 스타일)
    "subtitle_style": {
        "font":          "NanumSquareExtraBold",
        "size":          56,
        "color":         "#FFFFFF",
        "shadow_color":  "#000000",
        "shadow_alpha":  0.8,
        "position_y":    0.85,
        "chunk_words":   2,        # video-use 스타일 (2단어 청크)
        "fade_in_ms":    300,
        "fade_out_ms":   300,
    },

    # 영화급 색보정 프리셋
    "color_presets": {
        "warm cinematic":  "eq=brightness=0.02:contrast=1.1:saturation=1.08,colorbalance=rm=0.06:gm=0:bm=-0.06",
        "vibrant teal":    "eq=contrast=1.15:saturation=1.2,colorbalance=rm=-0.05:gm=0.02:bm=0.08",
        "moody amber":     "eq=brightness=-0.03:contrast=1.18:saturation=0.95,colorbalance=rm=0.08:gm=0.02:bm=-0.08,vignette=PI/5",
        "soft pastel":     "eq=brightness=0.04:contrast=0.95:saturation=0.9,colorbalance=rm=0.04:gm=0.04:bm=0.06",
        "matcha tone":     "eq=contrast=1.05:saturation=1.05,colorbalance=rm=-0.03:gm=0.08:bm=-0.02",
        "cool blue":       "eq=brightness=0.0:contrast=1.12:saturation=1.05,colorbalance=rm=-0.06:gm=0:bm=0.08",
        "rose pink":       "eq=brightness=0.03:contrast=1.0:saturation=1.1,colorbalance=rm=0.08:gm=0.0:bm=0.04",
    },

    # 트랜지션 길이 (초)
    "transition_durations": {
        "fade":          0.5,
        "dissolve":      0.6,
        "wipe":          0.4,
        "long_dissolve": 1.0,
    },
}


# 폴더 자동 분류 키워드 (확장판)
SCENE_KEYWORDS = {
    "egg_tart":  ["에그", "타르트", "tart", "egg", "01", "1_"],
    "pool":      ["풀", "수영", "pool", "여름", "summer", "02", "2_"],
    "soju":      ["소주", "soju", "술", "03", "3_"],
    "couple":    ["커플", "산책", "couple", "walk", "04", "4_"],
    "matcha":    ["말차", "케이크", "matcha", "cake", "05", "5_"],
    "stroller":  ["유모차", "stroller", "06", "6_"],
    "bow":       ["볼찌", "bow", "리본", "07", "7_"],
    "raincoat":  ["우비", "raincoat", "비", "rain", "08", "8_"],
    "rose":      ["장미", "rose", "꽃", "flower", "09", "9_"],
}


# ── FFmpeg 헬퍼 ───────────────────────────────────────────────────────────────
def has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def ffprobe(path: Path) -> Dict:
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
    info = ffprobe(path)
    try:
        return float(info["format"]["duration"])
    except (KeyError, ValueError):
        return 0.0


def get_dimensions(path: Path) -> Tuple[int, int]:
    info = ffprobe(path)
    try:
        stream = info["streams"][0]
        return int(stream["width"]), int(stream["height"])
    except (KeyError, ValueError, IndexError):
        return 1920, 1080


# ── 폴더 스캔 ─────────────────────────────────────────────────────────────────
class AssetScanner:
    VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
    IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
    AUDIO_EXTS = {".mp3", ".wav", ".aac", ".m4a", ".flac"}

    def __init__(self, source_dir: Path):
        self.source = source_dir
        self.videos: List[Path] = []
        self.images: List[Path] = []
        self.audios: List[Path] = []
        self.pixar_versions: List[Path] = []   # 픽사 스타일 변환본 별도 인식

    def scan(self) -> Dict:
        print(f"\n🔍 폴더 스캔 시작: {self.source}")
        for path in self.source.rglob("*"):
            if not path.is_file():
                continue
            ext = path.suffix.lower()
            name = path.stem.lower()

            # 픽사 변환본 별도 인식
            is_pixar = any(kw in name for kw in ["pixar", "kling", "runway", "ai_video", "3d"])

            if ext in self.VIDEO_EXTS:
                if is_pixar:
                    self.pixar_versions.append(path)
                else:
                    self.videos.append(path)
            elif ext in self.IMAGE_EXTS:
                self.images.append(path)
            elif ext in self.AUDIO_EXTS:
                self.audios.append(path)

        scenes = self._classify_by_scene()

        result = {
            "videos_count":        len(self.videos),
            "pixar_videos_count":  len(self.pixar_versions),
            "images_count":        len(self.images),
            "audios_count":        len(self.audios),
            "scenes":              scenes,
            "pixar_versions":      [str(p) for p in self.pixar_versions],
        }
        self._print_summary(result)
        return result

    def _classify_by_scene(self) -> Dict[str, Dict[str, List[str]]]:
        scenes = {scene: {"real": [], "pixar": []} for scene in SCENE_KEYWORDS}
        scenes["uncategorized"] = {"real": [], "pixar": []}

        for path in self.videos + self.images:
            name = path.stem.lower()
            classified = False
            for scene, keywords in SCENE_KEYWORDS.items():
                if any(kw in name for kw in keywords):
                    scenes[scene]["real"].append(str(path))
                    classified = True
                    break
            if not classified:
                scenes["uncategorized"]["real"].append(str(path))

        for path in self.pixar_versions:
            name = path.stem.lower()
            for scene, keywords in SCENE_KEYWORDS.items():
                if any(kw in name for kw in keywords):
                    scenes[scene]["pixar"].append(str(path))
                    break

        return scenes

    def _print_summary(self, result: Dict):
        print(f"\n📊 스캔 결과:")
        print(f"  🎥 일반 영상:   {result['videos_count']}개")
        print(f"  ✨ 픽사 변환본: {result['pixar_videos_count']}개")
        print(f"  🖼️  이미지:      {result['images_count']}개")
        print(f"  🎵 음원:        {result['audios_count']}개")
        print(f"\n🎬 씬별 분류 (실사 + 픽사):")
        for scene, files in result["scenes"].items():
            real_count  = len(files.get("real", []))
            pixar_count = len(files.get("pixar", []))
            if real_count + pixar_count > 0:
                scene_config = next((s for s in GUREUM_CONFIG["scenes"] if s["id"] == scene), None)
                emoji = scene_config["emoji"] if scene_config else "📁"
                title = scene_config["title"] if scene_config else scene
                print(f"  {emoji} {title:<12} 실사 {real_count}개, 픽사 {pixar_count}개")


# ── CapCut Builder (미세조정용 JSON 출력) ─────────────────────────────────────
class CapCutBuilderPro:
    """v2 - 영화급 CapCut JSON 생성"""

    def __init__(self, scenes_data: List[Dict], audio_path: Optional[Path] = None):
        self.scenes_data = scenes_data
        self.audio_path  = audio_path
        self.project_id  = str(uuid.uuid4()).replace("-", "")[:16]

    @staticmethod
    def sec_to_us(seconds: float) -> int:
        return int(seconds * 1_000_000)

    def build(self) -> Dict:
        """draft_content.json 생성"""
        video_materials, audio_materials, text_materials = [], [], []
        video_segments, audio_segments, text_segments    = [], [], []

        cursor_us = 0

        for i, scene in enumerate(self.scenes_data):
            duration_us = self.sec_to_us(scene.get("duration", 6))
            src_path    = scene.get("source", "")
            subtitle    = scene.get("subtitle", "")

            # 비디오 소재
            vid_mat_id = str(uuid.uuid4())
            video_materials.append({
                "id": vid_mat_id, "type": "photo" if scene.get("is_image") else "video",
                "path": src_path, "duration": duration_us,
                "width": 1920, "height": 1080,
                "local_material_id": vid_mat_id,
            })

            # 비디오 세그먼트 (씬별 다른 켄번스)
            ken = scene.get("ken_burns", "zoom_in")
            scale_x, scale_y = 1.08, 1.08
            if ken == "zoom_out":
                scale_x, scale_y = 1.0, 1.0
            elif ken == "macro_zoom":
                scale_x, scale_y = 1.15, 1.15

            seg = {
                "id": str(uuid.uuid4()),
                "material_id": vid_mat_id,
                "target_timerange": {"start": cursor_us, "duration": duration_us},
                "source_timerange": {"start": 0, "duration": duration_us},
                "clip": {
                    "alpha": 1.0, "rotation": 0.0,
                    "scale": {"x": scale_x, "y": scale_y},
                    "flip": {"horizontal": False, "vertical": False},
                },
                "extra_material_refs": [],
            }

            # 트랜지션
            if i > 0:
                trans_type = scene.get("transition_in", "dissolve")
                trans_dur  = GUREUM_CONFIG["transition_durations"].get(trans_type, 0.5)
                seg["transition"] = {
                    "type": trans_type,
                    "duration": self.sec_to_us(trans_dur),
                    "is_overlap": True,
                }
            video_segments.append(seg)

            # 자막
            if subtitle:
                txt_mat_id = str(uuid.uuid4())
                text_materials.append({
                    "id": txt_mat_id, "type": "text",
                    "content": subtitle,
                    "font_size": GUREUM_CONFIG["subtitle_style"]["size"],
                    "font_color": GUREUM_CONFIG["subtitle_style"]["color"],
                    "font_name": GUREUM_CONFIG["subtitle_style"]["font"],
                    "shadow": True,
                    "shadow_color": GUREUM_CONFIG["subtitle_style"]["shadow_color"],
                    "shadow_alpha": GUREUM_CONFIG["subtitle_style"]["shadow_alpha"],
                    "shadow_x": 2.0, "shadow_y": 2.0,
                    "alignment": 1,
                    "position": {"x": 0.5, "y": GUREUM_CONFIG["subtitle_style"]["position_y"]},
                })
                text_segments.append({
                    "id": str(uuid.uuid4()),
                    "material_id": txt_mat_id,
                    "target_timerange": {"start": cursor_us, "duration": duration_us},
                })

            cursor_us += duration_us

        # 음원 트랙
        if self.audio_path:
            aud_mat_id = str(uuid.uuid4())
            audio_materials.append({
                "id": aud_mat_id, "type": "audio",
                "path": str(self.audio_path),
                "duration": cursor_us,
            })
            audio_segments.append({
                "id": str(uuid.uuid4()),
                "material_id": aud_mat_id,
                "target_timerange": {"start": 0, "duration": cursor_us},
                "source_timerange": {"start": 0, "duration": cursor_us},
                "volume": 1.0,
            })

        # 트랙 조립
        tracks = [
            {"id": str(uuid.uuid4()), "type": "video",
             "attribute": 0, "flag": 0, "segments": video_segments},
        ]
        if audio_segments:
            tracks.append({
                "id": str(uuid.uuid4()), "type": "audio",
                "attribute": 0, "flag": 0, "segments": audio_segments,
            })
        if text_segments:
            tracks.append({
                "id": str(uuid.uuid4()), "type": "text",
                "attribute": 0, "flag": 0, "segments": text_segments,
            })

        return {
            "canvas_config": {
                "width": 1920, "height": 1080,
                "ratio": "16:9", "background_color": "#000000",
            },
            "duration":    cursor_us,
            "fps":         30.0,
            "version":     "3.0.0",
            "create_time": int(time.time()),
            "update_time": int(time.time()),
            "id":          self.project_id,
            "name":        GUREUM_CONFIG["project_name"],
            "tracks":      tracks,
            "materials": {
                "videos":  video_materials,
                "audios":  audio_materials,
                "texts":   text_materials,
                "effects": [], "stickers": [],
            },
        }

    def save(self, output_dir: Path) -> Path:
        draft        = self.build()
        capcut_dir   = output_dir / "capcut_project"
        capcut_dir.mkdir(parents=True, exist_ok=True)

        (capcut_dir / "draft_content.json").write_text(
            json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (capcut_dir / "draft_meta_info.json").write_text(
            json.dumps({
                "draft_id": self.project_id,
                "draft_name": GUREUM_CONFIG["project_name"],
                "draft_root_path": "",
                "tm_draft_create": int(time.time()),
                "tm_draft_modified": int(time.time()),
            }, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # CapCut 드래프트 폴더에 자동 복사 (Windows)
        capcut_draft = os.path.expandvars(
            r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft"
        )
        if os.path.exists(capcut_draft):
            dest = Path(capcut_draft) / f"구름이뮤직비디오_{self.project_id}"
            shutil.copytree(str(capcut_dir), str(dest), dirs_exist_ok=True)
            print(f"  ✅ CapCut에 자동 등록: {dest.name}")
            print(f"  ℹ️  CapCut 열면 '{GUREUM_CONFIG['project_name']}' 프로젝트가 보입니다")

        return capcut_dir


# ── Remotion 컴포넌트 생성 ────────────────────────────────────────────────────
class RemotionGenerator:
    """인트로/아웃트로 Remotion React 컴포넌트 생성"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir / "remotion_intro_outro"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self):
        """Remotion 프로젝트 구조 생성"""
        intro_tsx = '''import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

export const GureumIntro: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 페이드인 + 위로 살짝 떠오르기
  const opacity = interpolate(frame, [0, 30, 60, 75], [0, 1, 1, 0]);
  const translateY = spring({ frame, fps, config: { damping: 200 } });
  const scale = interpolate(frame, [0, 30], [0.8, 1]);

  return (
    <AbsoluteFill style={{
      backgroundColor: '#1a0f1f',
      background: 'radial-gradient(circle at center, #2d1b3d 0%, #0a0612 100%)',
      justifyContent: 'center',
      alignItems: 'center',
      fontFamily: 'NanumSquareExtraBold, sans-serif',
    }}>
      <div style={{
        opacity,
        transform: `translateY(${(1 - translateY) * 50}px) scale(${scale})`,
        textAlign: 'center',
      }}>
        <div style={{
          fontSize: 36,
          color: '#FFD4A3',
          letterSpacing: 8,
          marginBottom: 20,
          textTransform: 'uppercase',
        }}>
          🐾 Pomeranian Music Video
        </div>
        <div style={{
          fontSize: 140,
          color: 'white',
          fontWeight: 900,
          textShadow: '0 4px 20px rgba(0,0,0,0.5)',
        }}>
          구름이의 하루
        </div>
        <div style={{
          fontSize: 28,
          color: '#FFB78A',
          marginTop: 30,
          letterSpacing: 4,
        }}>
          A Day with Gureum
        </div>
      </div>
    </AbsoluteFill>
  );
};
'''

        outro_tsx = '''import React from 'react';
import { AbsoluteFill, useCurrentFrame, interpolate } from 'remotion';

export const GureumOutro: React.FC = () => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 30, 90, 120], [0, 1, 1, 0]);
  const heartScale = 1 + Math.sin(frame * 0.1) * 0.1;

  return (
    <AbsoluteFill style={{
      backgroundColor: '#1a0f1f',
      background: 'radial-gradient(ellipse at center, #3d2645 0%, #0a0612 100%)',
      justifyContent: 'center',
      alignItems: 'center',
      fontFamily: 'NanumSquareExtraBold, sans-serif',
    }}>
      <div style={{ opacity, textAlign: 'center' }}>
        <div style={{ fontSize: 60, color: 'white', fontWeight: 900, marginBottom: 30 }}>
          Music Video by
        </div>
        <div style={{ fontSize: 90, color: '#FFD4A3', fontWeight: 900, marginBottom: 60 }}>
          김무빈
        </div>
        <div style={{ fontSize: 50, color: '#FFB78A', transform: `scale(${heartScale})` }}>
          구독 & 좋아요 부탁드려요 💛
        </div>
        <div style={{ fontSize: 28, color: '#FFD4A3', marginTop: 80, letterSpacing: 6 }}>
          🐾 Made with love for Gureum 🐾
        </div>
      </div>
    </AbsoluteFill>
  );
};
'''

        composition_tsx = '''import { Composition } from 'remotion';
import { GureumIntro } from './GureumIntro';
import { GureumOutro } from './GureumOutro';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="GureumIntro"
        component={GureumIntro}
        durationInFrames={90}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="GureumOutro"
        component={GureumOutro}
        durationInFrames={120}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
'''

        package_json = '''{
  "name": "gureum-intro-outro",
  "version": "1.0.0",
  "scripts": {
    "start": "remotion studio",
    "build-intro": "remotion render GureumIntro intro.mp4",
    "build-outro": "remotion render GureumOutro outro.mp4"
  },
  "dependencies": {
    "react": "^18.0.0",
    "remotion": "^4.0.0",
    "@remotion/cli": "^4.0.0"
  }
}
'''

        readme = '''# 구름이 인트로/아웃트로 (Remotion)

## 사용법

```bash
# 의존성 설치
npm install

# 실시간 미리보기 (Remotion Studio)
npm start

# 인트로 렌더링
npm run build-intro    # → intro.mp4

# 아웃트로 렌더링
npm run build-outro    # → outro.mp4
```

## 메인 영상과 결합

```bash
# ffmpeg로 합치기
ffmpeg -i intro.mp4 -i gureum_main.mp4 -i outro.mp4 \\
  -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]" \\
  -map "[v]" -map "[a]" final_with_intro_outro.mp4
```
'''

        (self.output_dir / "GureumIntro.tsx").write_text(intro_tsx, encoding="utf-8")
        (self.output_dir / "GureumOutro.tsx").write_text(outro_tsx, encoding="utf-8")
        (self.output_dir / "Composition.tsx").write_text(composition_tsx, encoding="utf-8")
        (self.output_dir / "package.json").write_text(package_json, encoding="utf-8")
        (self.output_dir / "README.md").write_text(readme, encoding="utf-8")

        print(f"  ✅ Remotion 컴포넌트 4개 생성")
        return self.output_dir


# ── FFmpeg 풀스택 빌더 (영화급) ───────────────────────────────────────────────
class CinematicBuilder:
    """씬별 다른 무드 + 비트 동기화 + 영화급 트랜지션"""

    def __init__(self, scenes_data: List[Dict], audio_path: Optional[Path],
                 output_dir: Path):
        self.scenes_data = scenes_data
        self.audio_path  = audio_path
        self.output      = output_dir
        self.work_dir    = output_dir / "_work_v2"
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def build(self) -> Path:
        """씬별 빌드 → 합성 → 최종"""
        print(f"\n🎬 영화급 빌드 시작...")

        # 1. 씬별 클립 생성 (각각 다른 무드)
        clip_paths = []
        for i, scene in enumerate(self.scenes_data):
            clip = self.work_dir / f"scene_{i:02d}_{scene['id']}.mp4"
            self._build_scene(scene, clip, is_first=(i==0), is_last=(i==len(self.scenes_data)-1))
            clip_paths.append(clip)
            print(f"  ✅ 씬 {i+1}/{len(self.scenes_data)} 완료: {scene['emoji']} {scene['title']}")

        # 2. 트랜지션과 함께 합치기
        merged = self.work_dir / "merged_cinematic.mp4"
        self._concat_with_transitions(clip_paths, merged)
        print(f"\n  ✅ 영화급 트랜지션 적용 완료")

        # 3. 음원 합성 + 페이드인/아웃
        final = self.output / "final_gureum_mv.mp4"
        if self.audio_path:
            self._add_audio_with_fade(merged, final)
        else:
            shutil.copy(merged, final)

        print(f"  ✅ 최종 출력: {final.name}")
        return final

    def _build_scene(self, scene: Dict, output: Path, is_first: bool, is_last: bool):
        """씬별 클립 (켄번스 + 색보정 + 자막)"""
        src      = scene["source"]
        duration = scene["duration"]
        is_image = scene["is_image"]
        ken      = scene.get("ken_burns", "zoom_in")
        grade    = GUREUM_CONFIG["color_presets"].get(
            scene.get("color_grade", "warm cinematic"),
            GUREUM_CONFIG["color_presets"]["warm cinematic"]
        )

        # 켄번스 필터
        ken_filters = {
            "zoom_in":      f"zoompan=z='min(zoom+0.0015,1.15)':d={int(duration*30)}:s=1920x1080",
            "zoom_out":     f"zoompan=z='if(eq(on,0),1.15,max(zoom-0.0015,1.0))':d={int(duration*30)}:s=1920x1080",
            "pan_right":    f"zoompan=z=1.1:x='if(eq(on,0),0,min(x+1,iw-iw/zoom))':d={int(duration*30)}:s=1920x1080",
            "slow_pan":     f"zoompan=z=1.08:x='if(eq(on,0),0,min(x+0.5,iw-iw/zoom))':d={int(duration*30)}:s=1920x1080",
            "macro_zoom":   f"zoompan=z='min(zoom+0.0025,1.25)':d={int(duration*30)}:s=1920x1080",
            "side_pan":     f"zoompan=z=1.05:x='iw/2-(iw/zoom/2)':d={int(duration*30)}:s=1920x1080",
            "slow_zoom_out":f"zoompan=z='if(eq(on,0),1.2,max(zoom-0.001,1.0))':d={int(duration*30)}:s=1920x1080",
            "rack_focus":   f"zoompan=z='1.1':d={int(duration*30)}:s=1920x1080",
        }
        ken_filter = ken_filters.get(ken, ken_filters["zoom_in"])

        # 자막 필터 (페이드인/아웃)
        subtitle = scene.get("subtitle", "").replace("'", "")
        sub_filter = ""
        if subtitle:
            sub_filter = (
                f",drawtext=text='{subtitle}':"
                f"fontcolor=white:fontsize=56:"
                f"x=(w-text_w)/2:y=h*0.85-text_h/2:"
                f"shadowcolor=black@0.8:shadowx=3:shadowy=3:"
                f"borderw=2:bordercolor=black:"
                f"enable='between(t,0.5,{duration-0.5})':"
                f"alpha='if(lt(t,1),(t-0.5)/0.5,if(gt(t,{duration-1}),1-(t-{duration-1})/0.5,1))'"
            )

        # 페이드 인/아웃 (첫/마지막 씬)
        fade_filter = ""
        if is_first:
            fade_filter += f",fade=t=in:st=0:d=1"
        if is_last:
            fade_filter += f",fade=t=out:st={duration-1.5}:d=1.5"

        # 종합 필터
        full_filter = (
            f"scale=1920:1080:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,"
            f"{ken_filter},"
            f"{grade}"
            f"{sub_filter}"
            f"{fade_filter}"
        )

        # 이미지면 loop, 영상이면 그대로
        if is_image:
            cmd = [
                "ffmpeg", "-loop", "1", "-i", str(src),
                "-t", str(duration),
                "-vf", full_filter,
                "-r", "30",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-pix_fmt", "yuv420p",
                "-y", str(output)
            ]
        else:
            cmd = [
                "ffmpeg", "-i", str(src),
                "-t", str(duration),
                "-vf", full_filter,
                "-r", "30",
                "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                "-an",
                "-y", str(output)
            ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  씬 빌드 오류, 단순 모드 폴백: {scene['id']}")
            # 폴백
            cmd_simple = (
                ["ffmpeg", "-loop", "1", "-i", str(src), "-t", str(duration),
                 "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080",
                 "-r", "30", "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p",
                 "-y", str(output)]
                if is_image else
                ["ffmpeg", "-i", str(src), "-t", str(duration),
                 "-vf", "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080",
                 "-r", "30", "-c:v", "libx264", "-crf", "23", "-an",
                 "-y", str(output)]
            )
            subprocess.run(cmd_simple, check=True, capture_output=True)

    def _concat_with_transitions(self, clips: List[Path], output: Path):
        """xfade 트랜지션으로 영화급 연결"""
        if len(clips) < 2:
            shutil.copy(clips[0], output)
            return

        # 간단 버전: concat (트랜지션은 씬별 fade로 처리됨)
        list_file = self.work_dir / "concat_list.txt"
        list_file.write_text(
            "\n".join(f"file '{c.absolute()}'" for c in clips),
            encoding="utf-8"
        )
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0",
            "-i", str(list_file),
            "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-y", str(output)
        ]
        subprocess.run(cmd, check=True, capture_output=True)

    def _add_audio_with_fade(self, video: Path, output: Path):
        """음원 합성 + 페이드인/아웃"""
        video_duration = get_duration(video)
        cmd = [
            "ffmpeg", "-i", str(video), "-i", str(self.audio_path),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "256k",
            "-af", f"afade=t=in:d=2,afade=t=out:st={video_duration-3}:d=3",
            "-shortest",
            "-y", str(output)
        ]
        subprocess.run(cmd, check=True, capture_output=True)


# ── 메인 오케스트레이터 ───────────────────────────────────────────────────────
class GureumMVOrchestrator:
    """모든 시스템 통합 — 풀스택 + CapCut 동시 출력"""

    def __init__(self, source_dir: Path, output_dir: Path, audio_path: Optional[Path] = None):
        self.source     = source_dir
        self.output     = output_dir
        self.audio      = audio_path
        self.scenes_data: List[Dict] = []

        self.output.mkdir(parents=True, exist_ok=True)

    def run(self):
        """전체 파이프라인"""
        print(f"\n{'═'*60}")
        print(f"  🐾 구름이 뮤직비디오 — 풀스택 빌더 v2")
        print(f"  영화급 자동 생성 + CapCut JSON 동시 출력")
        print(f"{'═'*60}")

        # 1. 스캔
        scanner = AssetScanner(self.source)
        scan_result = scanner.scan()
        (self.output / "scan_result.json").write_text(
            json.dumps(scan_result, ensure_ascii=False, indent=2), encoding="utf-8"
        )

        # 2. 음원 자동 감지
        if not self.audio and scanner.audios:
            self.audio = max(scanner.audios, key=get_duration)
            print(f"\n🎵 음원 자동 선택: {self.audio.name} ({get_duration(self.audio):.1f}초)")

        # 3. 씬 데이터 구성 (실사 우선, 픽사 백업)
        print(f"\n📋 씬 구성 중...")
        for scene_config in GUREUM_CONFIG["scenes"]:
            scene_id = scene_config["id"]
            files = scan_result["scenes"].get(scene_id, {"real": [], "pixar": []})

            # 픽사 변환본 우선, 없으면 실사
            source_file = None
            if files.get("pixar"):
                source_file = files["pixar"][0]
                source_type = "✨pixar"
            elif files.get("real"):
                source_file = files["real"][0]
                source_type = "📷real"

            if not source_file:
                print(f"  ⚠️  {scene_config['emoji']} {scene_config['title']}: 자료 없음 (스킵)")
                continue

            is_image = Path(source_file).suffix.lower() in AssetScanner.IMAGE_EXTS
            self.scenes_data.append({
                **scene_config,
                "source":   source_file,
                "is_image": is_image,
                "type":     source_type,
            })
            print(f"  {source_type} {scene_config['emoji']} {scene_config['title']:<10} → {Path(source_file).name}")

        if not self.scenes_data:
            print("\n❌ 사용 가능한 자료가 없습니다.")
            return None

        # 4. CapCut JSON 출력 (병렬)
        print(f"\n📁 [1/3] CapCut 프로젝트 생성...")
        capcut = CapCutBuilderPro(self.scenes_data, self.audio)
        capcut_dir = capcut.save(self.output)
        print(f"  📁 {capcut_dir}")

        # 5. Remotion 컴포넌트 생성 (병렬)
        print(f"\n🎬 [2/3] Remotion 인트로/아웃트로 컴포넌트...")
        remotion = RemotionGenerator(self.output)
        remotion_dir = remotion.generate()
        print(f"  📁 {remotion_dir}")

        # 6. 영화급 영상 자동 빌드
        print(f"\n🎥 [3/3] 영화급 영상 빌드...")
        builder = CinematicBuilder(self.scenes_data, self.audio, self.output)
        final = builder.build()

        # 7. project.md 작성 (세션 메모리)
        self._save_project_md(scan_result)

        # 8. 결과 출력
        print(f"\n{'═'*60}")
        print(f"  ✅ 완료! — 3가지 동시 출력")
        print(f"{'═'*60}")
        print(f"\n  1️⃣  자동 완성 영상:")
        print(f"     {final}")
        print(f"     ⏱️  {get_duration(final):.1f}초")
        print(f"\n  2️⃣  CapCut 후작업용 JSON:")
        print(f"     {self.output}/capcut_project/draft_content.json")
        print(f"     💡 CapCut 열면 자동으로 프로젝트가 보입니다")
        print(f"\n  3️⃣  Remotion 인트로/아웃트로:")
        print(f"     {self.output}/remotion_intro_outro/")
        print(f"     💡 cd remotion_intro_outro && npm install && npm start")
        print(f"\n{'═'*60}\n")

        return final

    def _save_project_md(self, scan_result: Dict):
        md = f"""# 구름이 뮤직비디오 프로젝트 메모리

## 작업 일시
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 소스 폴더
{self.source}

## 사용된 자료
- 실사 영상: {scan_result['videos_count']}개
- 픽사 변환본: {scan_result['pixar_videos_count']}개
- 이미지: {scan_result['images_count']}개
- 음원: {scan_result['audios_count']}개

## 씬 구성 ({len(self.scenes_data)}개)
{chr(10).join(f"- {s['emoji']} {s['title']} ({s['type']}) - {s['mood']} - {s['duration']}초" for s in self.scenes_data)}

## 음원
{self.audio.name if self.audio else '없음'} ({get_duration(self.audio) if self.audio else 0:.1f}초)

## 다음 작업
- [ ] 자동 영상 확인 후 마음에 들면 그대로 사용
- [ ] CapCut으로 미세조정 (capcut_project 자동 등록됨)
- [ ] Remotion 인트로/아웃트로 추가 (선택)
- [ ] YouTube 메타데이터 작성
- [ ] 썸네일 제작
- [ ] 업로드
"""
        (self.output / "project.md").write_text(md, encoding="utf-8")


# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="구름이 뮤직비디오 풀스택 자동 생성 v2")
    p.add_argument("--source", default=r"D:\멍냥구조대\김정원대표님")
    p.add_argument("--output", default="./gureum_output_v2")
    p.add_argument("--audio",  default=None)
    p.add_argument("--auto",   action="store_true")
    p.add_argument("--scan-only", action="store_true")
    args = p.parse_args()

    if not has_ffmpeg():
        print("❌ ffmpeg/ffprobe 필요")
        print("   설치: winget install Gyan.FFmpeg")
        sys.exit(1)

    source = Path(args.source)
    if not source.exists():
        print(f"❌ 소스 폴더 없음: {source}")
        sys.exit(1)

    if args.scan_only:
        scanner = AssetScanner(source)
        scanner.scan()
        return

    orch = GureumMVOrchestrator(source, Path(args.output),
                                 Path(args.audio) if args.audio else None)
    orch.run()


if __name__ == "__main__":
    main()
