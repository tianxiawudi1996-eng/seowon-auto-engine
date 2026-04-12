"""
CapCut Builder — draft_content.json 자동 생성
=============================================
scenes.md → CapCut 프로젝트 JSON → CapCut 열면 즉시 완성본
"""
import json
import uuid
import shutil
import os
from pathlib import Path
from typing import List, Dict, Any


class CapCutBuilder:
    """CapCutAPI HTTP 서버 또는 직접 JSON 방식으로 편집 자동화"""

    # CapCutAPI 서버 주소 (로컬 실행 시)
    CAPCUT_API = "http://localhost:9001"

    # CapCut 드래프트 저장 경로 (Windows)
    DRAFT_DIR = os.path.expandvars(
        r"%LOCALAPPDATA%\CapCut\User Data\Projects\com.lveditor.draft"
    )

    def __init__(self, channel: str, workspace: Path, output: Path):
        self.channel = channel
        self.workspace = workspace
        self.output = output

        # 채널별 설정
        self.resolution = {
            "seowon":   (1920, 1080),
            "jusi":     (1080, 1920),
            "unspoken": (1080, 1920),
        }[channel]

    def run(self) -> Dict:
        """씬 데이터 → CapCut JSON 생성"""
        print(f"  🎬 EDITOR: CapCut 프로젝트 생성 중...")

        # scenes.md 로드
        scenes_path = self.workspace / "scenes.md"
        scenes = self._load_scenes(scenes_path)

        # draft_content.json 생성
        draft = self._build_draft_json(scenes)

        # 프로젝트 폴더 생성
        project_id = str(uuid.uuid4()).replace("-", "")[:16]
        project_dir = self.output / "capcut_projects" / f"project_{project_id}"
        project_dir.mkdir(parents=True, exist_ok=True)

        # JSON 저장
        draft_path = project_dir / "draft_content.json"
        draft_path.write_text(
            json.dumps(draft, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # meta_info.json 생성
        meta = self._build_meta_json(project_id)
        (project_dir / "draft_meta_info.json").write_text(
            json.dumps(meta, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        print(f"  ✅ CapCut 프로젝트: {project_dir}")
        print(f"  💡 CapCut에서 열기: {project_dir} 를 드래프트 폴더에 복사하세요")

        return {
            "project_dir": str(project_dir),
            "draft_path": str(draft_path),
            "project_id": project_id,
        }

    def _load_scenes(self, path: Path) -> List[Dict]:
        """scenes.md에서 씬 데이터 파싱"""
        if not path.exists():
            # 기본 테스트 씬 반환
            return [
                {"scene": 1, "text": "테스트 씬", "image_keyword": "construction safety",
                 "subtitle": "테스트", "duration": 6},
            ]
        try:
            content = path.read_text(encoding="utf-8").strip()
            return json.loads(content)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 기본값
            return [{"scene": 1, "text": "씬 파싱 실패", "duration": 6}]

    def _build_draft_json(self, scenes: List[Dict]) -> Dict:
        """CapCut draft_content.json 전체 구조 생성"""
        w, h = self.resolution
        tracks = []
        materials_videos = []
        materials_audios = []
        materials_texts = []

        cursor_us = 0  # 마이크로초 커서

        for i, scene in enumerate(scenes):
            duration_us = int(scene.get("duration", 6) * 1_000_000)
            mat_id = str(uuid.uuid4())
            seg_id = str(uuid.uuid4())

            # 이미지 경로 (실제 경로로 대체)
            image_path = str(self.workspace / "scenes" / f"scene_{i+1:02d}.jpg")
            audio_path = str(self.workspace / "audio" / f"voice_{i+1:02d}.mp3")

            # 비디오(이미지) 소재
            materials_videos.append({
                "id": mat_id,
                "type": "photo",
                "path": image_path,
                "duration": duration_us,
                "width": w,
                "height": h,
            })

            # 자막 소재
            subtitle_text = scene.get("subtitle", scene.get("text", ""))
            text_id = str(uuid.uuid4())
            materials_texts.append({
                "id": text_id,
                "content": subtitle_text,
                "font_size": 42 if h > w else 36,  # 세로/가로 대응
                "font_color": "#FFFFFF",
                "font_name": "NanumGothic",
                "shadow": True,
                "shadow_color": "#000000",
                "shadow_opacity": 0.7,
                "alignment": 2,  # 하단 중앙
            })

            cursor_us += duration_us

        # 비디오 트랙
        video_segments = []
        cursor_us = 0
        for i, (scene, mat) in enumerate(zip(scenes, materials_videos)):
            duration_us = int(scene.get("duration", 6) * 1_000_000)
            video_segments.append({
                "id": str(uuid.uuid4()),
                "material_id": mat["id"],
                "target_timerange": {"start": cursor_us, "duration": duration_us},
                "source_timerange": {"start": 0, "duration": duration_us},
                "clip": {
                    "scale": {"x": 1.05, "y": 1.05},  # 켄번스 효과
                    "rotation": 0,
                },
                "transition": {
                    "type": "dissolve",
                    "duration": 500_000,  # 0.5초
                } if i > 0 else None,
            })
            cursor_us += duration_us

        tracks.append({
            "id": str(uuid.uuid4()),
            "type": "video",
            "attribute": 0,
            "segments": [s for s in video_segments if s],
        })

        # 자막 트랙
        subtitle_segments = []
        cursor_us = 0
        for scene, txt_mat in zip(scenes, materials_texts):
            duration_us = int(scene.get("duration", 6) * 1_000_000)
            subtitle_segments.append({
                "id": str(uuid.uuid4()),
                "material_id": txt_mat["id"],
                "target_timerange": {"start": cursor_us, "duration": duration_us},
            })
            cursor_us += duration_us

        tracks.append({
            "id": str(uuid.uuid4()),
            "type": "text",
            "attribute": 0,
            "segments": subtitle_segments,
        })

        total_duration = sum(int(s.get("duration", 6) * 1_000_000) for s in scenes)

        return {
            "canvas_config": {
                "width": w,
                "height": h,
                "ratio": f"{w}:{h}",
                "background_color": "#000000",
            },
            "duration": total_duration,
            "fps": 30,
            "tracks": tracks,
            "materials": {
                "videos": materials_videos,
                "audios": materials_audios,
                "texts": materials_texts,
            },
            "version": "3.0.0",
        }

    def _build_meta_json(self, project_id: str) -> Dict:
        return {
            "draft_id": project_id,
            "draft_name": f"SEOWON_AUTO_{self.channel.upper()}",
            "draft_root_path": "",
            "create_time": 0,
            "update_time": 0,
        }

    def copy_to_capcut(self, project_dir: Path):
        """생성된 프로젝트를 CapCut 드래프트 폴더로 복사"""
        if os.path.exists(self.DRAFT_DIR):
            dest = Path(self.DRAFT_DIR) / project_dir.name
            shutil.copytree(str(project_dir), str(dest))
            print(f"  ✅ CapCut 드래프트 폴더로 복사 완료: {dest}")
        else:
            print(f"  ⚠️  CapCut 드래프트 폴더 없음. 수동 복사 필요: {project_dir}")
