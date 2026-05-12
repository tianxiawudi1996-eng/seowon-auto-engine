"""
env_detector.py — 환경 자동 감지 & 권한 분리
=================================================
김무빈 차장의 다중 디바이스 환경을 자동으로 인식하고,
각 환경에 맞는 채널 권한 및 리소스 제약을 적용한다.

원칙:
  - 회사 PC (사무실 Galaxy Book5) = 3채널 전부 작업 가능
  - 개인 PC (집 Xeon 데스크탑)    = 개인 채널만 (서원토건 금지)
  - 노트북/태블릿                  = 개인 채널만

외부 의존성: ZERO (Python stdlib 전용)
"""

import os
import sys
import json
import socket
import platform
import getpass
from pathlib import Path
from datetime import datetime


# ── 환경 프로필 정의 ──────────────────────────────────────────────────────────
ENV_PROFILES = {
    "office_galaxy_book5": {
        "device_name":     "Galaxy Book5 Ultra",
        "location":        "사무실",
        "username_match":  ["seowo"],
        "cpu_class":       "intel_arc_140v",
        "ram_gb":          32,
        "gpu":             "Intel Arc 140V (iGPU)",
        "allowed_channels": ["seowon", "jusi", "unspoken"],
        "denied_channels": [],
        "preferred_tasks": ["coding", "test", "synthesis"],
        "batch_capable":   False,
        "ffmpeg_threads":  8,
        "max_concurrent":  2,
    },
    "home_xeon_desktop": {
        "device_name":     "Xeon E5-2683v4 Desktop",
        "location":        "집",
        "username_match":  ["ddedi"],
        "cpu_class":       "xeon_e5_2683v4",
        "ram_gb":          64,
        "gpu":             "GTX 960 2GB",
        "allowed_channels": ["jusi", "unspoken"],
        "denied_channels": ["seowon"],
        "preferred_tasks": ["batch_encoding", "ffmpeg_heavy", "synthesis"],
        "batch_capable":   True,
        "ffmpeg_threads":  16,
        "max_concurrent":  4,
    },
    "mobile_or_tablet": {
        "device_name":     "Galaxy S24 Ultra / Tab S9 Ultra",
        "location":        "이동중",
        "username_match":  [],
        "cpu_class":       "mobile_arm",
        "ram_gb":          12,
        "gpu":             "Adreno (모바일)",
        "allowed_channels": ["jusi", "unspoken"],
        "denied_channels": ["seowon"],
        "preferred_tasks": ["planning", "review"],
        "batch_capable":   False,
        "ffmpeg_threads":  4,
        "max_concurrent":  1,
    },
    "unknown": {
        "device_name":     "Unknown Device",
        "location":        "알 수 없음",
        "username_match":  [],
        "allowed_channels": ["jusi", "unspoken"],  # 안전 기본값
        "denied_channels": ["seowon"],
        "preferred_tasks": ["safe_mode"],
        "batch_capable":   False,
        "ffmpeg_threads":  2,
        "max_concurrent":  1,
    },
}


class EnvironmentDetector:
    """현재 환경을 자동 감지하고 권한을 반환"""

    def __init__(self):
        self.username = getpass.getuser().lower()
        self.hostname = socket.gethostname().lower()
        self.os       = platform.system()
        self.platform = platform.platform()
        self.profile  = self._detect()

    def _detect(self) -> dict:
        """username 기반으로 프로필 매칭"""
        for env_id, profile in ENV_PROFILES.items():
            if env_id == "unknown":
                continue
            for match in profile["username_match"]:
                if match in self.username:
                    return {**profile, "env_id": env_id}
        return {**ENV_PROFILES["unknown"], "env_id": "unknown"}

    def can_use_channel(self, channel: str) -> bool:
        """채널 사용 권한 체크"""
        return channel in self.profile["allowed_channels"]

    def enforce_channel(self, channel: str):
        """채널 권한 강제 (위반 시 에러)"""
        if not self.can_use_channel(channel):
            print("\n" + "=" * 60)
            print(f"  ⛔ 권한 차단 — 이 디바이스에서 '{channel}' 채널 작업 금지")
            print("=" * 60)
            print(f"  환경: {self.profile['device_name']} ({self.profile['location']})")
            print(f"  허용 채널: {self.profile['allowed_channels']}")
            print(f"  거부 채널: {self.profile['denied_channels']}")
            print(f"  이유: 회사/개인 프로젝트 분리 원칙")
            print("=" * 60 + "\n")
            sys.exit(1)

    def info(self) -> dict:
        """환경 전체 정보"""
        return {
            "detected_at":     datetime.now().isoformat(),
            "username":        self.username,
            "hostname":        self.hostname,
            "os":              self.os,
            "platform":        self.platform,
            "env_id":          self.profile["env_id"],
            "device_name":     self.profile["device_name"],
            "location":        self.profile["location"],
            "allowed_channels": self.profile["allowed_channels"],
            "denied_channels": self.profile["denied_channels"],
            "ffmpeg_threads":  self.profile["ffmpeg_threads"],
            "max_concurrent":  self.profile["max_concurrent"],
            "batch_capable":   self.profile["batch_capable"],
        }

    def print_banner(self):
        """환경 정보 배너 출력"""
        p = self.profile
        print("\n" + "═" * 60)
        print(f"  🎬 SEOWON-AUTO ENGINE v3.0 — 환경 감지")
        print("═" * 60)
        print(f"  📍 위치:        {p['location']}")
        print(f"  💻 디바이스:    {p['device_name']}")
        print(f"  👤 사용자:      {self.username}@{self.hostname}")
        print(f"  🖥️  OS:          {self.os}")
        print(f"  ✅ 허용 채널:   {', '.join(p['allowed_channels'])}")
        if p['denied_channels']:
            print(f"  ⛔ 차단 채널:   {', '.join(p['denied_channels'])}")
        print(f"  ⚡ ffmpeg 스레드: {p['ffmpeg_threads']}개 (동시 작업 {p['max_concurrent']}개)")
        print(f"  🌙 야간 배치:    {'가능' if p['batch_capable'] else '불가'}")
        print("═" * 60 + "\n")


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    detector = EnvironmentDetector()
    detector.print_banner()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "info":
            print(json.dumps(detector.info(), ensure_ascii=False, indent=2))
        elif cmd == "check" and len(sys.argv) > 2:
            channel = sys.argv[2]
            allowed = detector.can_use_channel(channel)
            print(f"채널 '{channel}': {'✅ 허용' if allowed else '⛔ 거부'}")
            sys.exit(0 if allowed else 1)
        elif cmd == "enforce" and len(sys.argv) > 2:
            detector.enforce_channel(sys.argv[2])
            print(f"✅ 채널 '{sys.argv[2]}' 권한 확인")
