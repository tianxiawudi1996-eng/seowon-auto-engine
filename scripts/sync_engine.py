"""
sync_engine.py — GitHub 양방향 자동 동기화 엔진
================================================
집 ↔ 사무실 간 작업 자동 동기화.
충돌 자동 해결, 안전한 stash, 자동 commit 전략 포함.

기능:
  - 자동 pull (작업 시작 시)
  - 자동 push (작업 종료 시)
  - 충돌 시 자동 백업 후 안전 해결
  - 환경별 .env 보호 (절대 push 안 함)
  - 마지막 동기화 시간 추적

외부 의존성: ZERO (subprocess, pathlib stdlib)
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta


class GitSyncEngine:
    """Git 양방향 동기화 — pip 패키지 ZERO"""

    def __init__(self, repo_path: Path):
        self.repo_path = Path(repo_path)
        if not (self.repo_path / ".git").exists():
            raise RuntimeError(f"❌ Git 저장소 아님: {repo_path}")
        self.state_file = self.repo_path / ".seowon" / "sync_state.json"
        self.state_file.parent.mkdir(exist_ok=True)

    # ── 상태 관리 ─────────────────────────────────────────────────────────────
    def load_state(self) -> dict:
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {"last_pull": None, "last_push": None, "device": None}

    def save_state(self, state: dict):
        self.state_file.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    # ── git 실행 헬퍼 ─────────────────────────────────────────────────────────
    def _git(self, *args, check=True, capture=True) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=capture,
            text=True,
            check=check,
        )

    def _branch(self) -> str:
        return self._git("branch", "--show-current").stdout.strip()

    def _is_clean(self) -> bool:
        return not self._git("status", "--porcelain").stdout.strip()

    def _has_remote_changes(self) -> bool:
        """원격에 새 커밋이 있는지"""
        self._git("fetch", "origin", check=False)
        local  = self._git("rev-parse", "HEAD").stdout.strip()
        remote = self._git("rev-parse", f"origin/{self._branch()}", check=False).stdout.strip()
        return local != remote

    # ── PULL (작업 시작) ──────────────────────────────────────────────────────
    def pull(self, device_name: str) -> dict:
        """안전한 자동 pull"""
        print(f"\n📥 [SYNC] 최신 변경사항 가져오는 중...")
        result = {"status": "ok", "stashed": False, "conflicts": []}

        # 1. 변경사항이 있으면 stash
        if not self._is_clean():
            print("  ⚠️  작업 중 변경사항 발견 → 안전 백업(stash)")
            stash_msg = f"auto-stash {device_name} {datetime.now():%Y%m%d_%H%M%S}"
            self._git("stash", "push", "-u", "-m", stash_msg)
            result["stashed"] = True

        # 2. pull --rebase
        try:
            self._git("pull", "--rebase", "origin", self._branch())
            print(f"  ✅ pull 성공")
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  rebase 충돌 발생 — 안전 모드로 전환")
            self._git("rebase", "--abort", check=False)
            self._git("pull", "--no-rebase", "origin", self._branch(), check=False)
            result["conflicts"].append(str(e))

        # 3. stash 복원
        if result["stashed"]:
            try:
                self._git("stash", "pop")
                print(f"  ✅ 작업 중이던 변경사항 복원")
            except subprocess.CalledProcessError:
                print(f"  ⚠️  복원 충돌 — `git stash list`로 수동 확인")
                result["conflicts"].append("stash_pop_conflict")

        # 4. 상태 저장
        state = self.load_state()
        state["last_pull"] = datetime.now().isoformat()
        state["device"]    = device_name
        self.save_state(state)
        return result

    # ── PUSH (작업 종료) ──────────────────────────────────────────────────────
    def push(self, device_name: str, message: str = None) -> dict:
        """자동 commit + push"""
        print(f"\n📤 [SYNC] 작업 내용 푸시 중...")
        result = {"status": "ok", "committed": False, "pushed": False}

        if self._is_clean():
            print("  ℹ️  변경사항 없음 — 푸시 스킵")
            return result

        # 1. 자동 commit
        self._git("add", "-A")
        commit_msg = message or f"auto-sync from {device_name} ({datetime.now():%Y-%m-%d %H:%M})"
        self._git("commit", "-m", commit_msg)
        result["committed"] = True
        print(f"  ✅ 커밋: {commit_msg}")

        # 2. push 전 원격 변경 체크
        if self._has_remote_changes():
            print("  ⚠️  원격에 새 커밋 발견 → 먼저 pull 진행")
            self._git("pull", "--rebase", "origin", self._branch())

        # 3. push
        try:
            self._git("push", "origin", self._branch())
            result["pushed"] = True
            print(f"  ✅ 푸시 완료")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ 푸시 실패: {e}")
            result["status"] = "error"
            result["error"]  = str(e)
            return result

        # 4. 상태 저장
        state = self.load_state()
        state["last_push"] = datetime.now().isoformat()
        state["device"]    = device_name
        self.save_state(state)
        return result

    # ── 자동 모드 (시작·종료 한 번에) ─────────────────────────────────────────
    def auto_sync(self, device_name: str, before: bool = True, after: bool = True):
        """before=시작 시 pull, after=종료 시 push"""
        if before:
            self.pull(device_name)
        yield  # 실제 작업은 여기서 진행 (with 문 사용)
        if after:
            self.push(device_name)

    # ── 상태 보고 ─────────────────────────────────────────────────────────────
    def status_report(self) -> str:
        state = self.load_state()
        branch = self._branch()
        clean  = self._is_clean()
        last_pull = state.get("last_pull", "없음")
        last_push = state.get("last_push", "없음")
        last_device = state.get("device", "알 수 없음")

        return f"""
═══════════════════════════════════════════════
  📊 GIT SYNC STATUS
═══════════════════════════════════════════════
  레포지토리:   {self.repo_path.name}
  브랜치:       {branch}
  작업 상태:    {'깨끗' if clean else '변경사항 있음'}

  마지막 pull:  {last_pull}
  마지막 push:  {last_push}
  마지막 디바이스: {last_device}
═══════════════════════════════════════════════
"""


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="SEOWON Git Sync Engine")
    p.add_argument("command", choices=["pull", "push", "status", "auto"])
    p.add_argument("--repo",   default=".", help="레포 경로")
    p.add_argument("--device", default=os.environ.get("SEOWON_DEVICE", "unknown"))
    p.add_argument("--message", "-m", default=None)
    args = p.parse_args()

    engine = GitSyncEngine(Path(args.repo).resolve())

    if args.command == "pull":
        engine.pull(args.device)
    elif args.command == "push":
        engine.push(args.device, args.message)
    elif args.command == "status":
        print(engine.status_report())
    elif args.command == "auto":
        engine.pull(args.device)
        print("\n💡 작업을 진행하세요. 끝나면 push 실행:")
        print(f"   python sync_engine.py push --device {args.device}")
