"""
master.py — SEOWON-AUTO ENGINE 통합 진입점
============================================
환경 감지 → 권한 체크 → 자동 sync → 작업 실행 → 자동 push → 알림
한 줄 명령으로 모든 자동화를 처리한다.

사용:
  # 즉시 실행 (단일 작업)
  python master.py run --channel jusi --topic "시니어가 절대 안 알려주는 것들"

  # 배치 큐 추가
  python master.py queue --channel unspoken --topic "비 오는 새벽"

  # 야간 배치 실행
  python master.py batch

  # 동기화만
  python master.py sync

  # 상태 보기
  python master.py status

외부 의존성: ZERO
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# 같은 폴더의 모듈들
sys.path.insert(0, str(Path(__file__).parent))
from env_detector import EnvironmentDetector
from sync_engine  import GitSyncEngine
from batch_runner import BatchRunner
from notifier     import Notifier


ROOT = Path(__file__).parent.parent


class SeowonMaster:
    """통합 진입점 — 모든 모듈 조율"""

    def __init__(self):
        # 1. 환경 감지
        self.env = EnvironmentDetector()
        self.env.print_banner()

        # 2. 환경변수 자동 주입
        os.environ["SEOWON_DEVICE"]         = self.env.profile["env_id"]
        os.environ["SEOWON_MAX_CONCURRENT"] = str(self.env.profile["max_concurrent"])
        os.environ["FFMPEG_THREADS"]        = str(self.env.profile["ffmpeg_threads"])

        # 3. 모듈 초기화
        self.notifier = Notifier()
        try:
            self.sync = GitSyncEngine(ROOT)
        except Exception:
            self.sync = None
            print("  ⚠️  Git 저장소가 아님 — sync 기능 비활성화")

        self.batch = BatchRunner(ROOT / "data" / "batch_queue.json",
                                 max_workers=self.env.profile["max_concurrent"])

    # ── 단일 작업 실행 ────────────────────────────────────────────────────────
    def run(self, channel: str, topic: str, mode: str = "synthesis",
            auto_sync: bool = True, notify: bool = True):
        """단일 작업 즉시 실행"""
        # 권한 체크
        self.env.enforce_channel(channel)

        # 동기화 (pull)
        if auto_sync and self.sync:
            self.sync.pull(self.env.profile["env_id"])

        # 알림 — 시작
        if notify:
            self.notifier.job_started(f"realtime", channel, topic)

        # 실제 실행
        cmd = self._build_command(channel, topic, mode)
        print(f"\n🚀 실행: {' '.join(cmd)}\n")
        result = subprocess.run(cmd, cwd=ROOT)

        # 알림 — 완료
        if notify:
            output_dir = str(ROOT / "output")
            if result.returncode == 0:
                self.notifier.job_done(f"realtime", channel, topic, output_dir)
            else:
                self.notifier.error(
                    f"작업 실패 (exit {result.returncode})",
                    f"channel={channel}\ntopic={topic}"
                )

        # 동기화 (push)
        if auto_sync and self.sync and result.returncode == 0:
            self.sync.push(
                self.env.profile["env_id"],
                f"feat: {channel} 영상 자동생성 - {topic}"
            )

        return result.returncode

    # ── 배치 큐 추가 ──────────────────────────────────────────────────────────
    def queue(self, channel: str, topic: str, mode: str = "synthesis",
              priority: int = 5):
        """배치 큐에 추가"""
        self.env.enforce_channel(channel)
        cmd = " ".join(self._build_command(channel, topic, mode))
        job_id = self.batch.add({
            "channel":  channel,
            "topic":    topic,
            "mode":     mode,
            "command":  cmd,
            "priority": priority,
        })
        print(f"\n✅ 큐 추가 완료 — {job_id}")
        print(f"   채널:    {channel}")
        print(f"   주제:    {topic}")
        print(f"   우선순위: {priority}")
        print(f"\n💡 야간 배치 실행: python master.py batch")

    # ── 배치 실행 ─────────────────────────────────────────────────────────────
    def run_batch(self, auto_sync: bool = True, notify: bool = True):
        """야간 배치 — 큐에 있는 작업 전부 실행"""
        if not self.env.profile["batch_capable"]:
            print("⚠️  이 디바이스는 배치 작업 비추천 — 그래도 진행합니다")

        # Pull
        if auto_sync and self.sync:
            self.sync.pull(self.env.profile["env_id"])

        # 큐 실행
        import time
        start = time.time()
        queued_count = len(self.batch.get_queued())
        if notify:
            self.notifier.notify(
                f"📥 작업 {queued_count}개 시작\n💻 {self.env.profile['device_name']}",
                title="🌙 야간 배치 시작", level="info"
            )
        self.batch.run_all()
        elapsed_min = (time.time() - start) / 60

        # 결과 집계
        jobs = self.batch.load_queue()
        done   = sum(1 for j in jobs if j["status"] == "done")
        failed = sum(1 for j in jobs if j["status"] == "failed")

        # 알림
        if notify:
            self.notifier.batch_completed(
                total=queued_count, done=done, failed=failed,
                elapsed_min=elapsed_min,
                output_dir=str(ROOT / "output"),
            )

        # Push
        if auto_sync and self.sync:
            self.sync.push(
                self.env.profile["env_id"],
                f"batch: {done}편 완료, {failed}편 실패"
            )

    # ── 동기화만 ──────────────────────────────────────────────────────────────
    def sync_only(self):
        if not self.sync:
            print("❌ Git 저장소가 아닙니다.")
            return
        self.sync.pull(self.env.profile["env_id"])
        self.sync.push(self.env.profile["env_id"])

    # ── 상태 ──────────────────────────────────────────────────────────────────
    def status(self):
        if self.sync:
            print(self.sync.status_report())
        self.batch.report()

    # ── 헬퍼 ──────────────────────────────────────────────────────────────────
    def _build_command(self, channel: str, topic: str, mode: str) -> list:
        """orchestrator.py 실행 명령 생성"""
        orchestrator = ROOT / "src" / "orchestrator.py"
        if not orchestrator.exists():
            # 폴백: zero_server.py
            orchestrator = ROOT / "src" / "zero_server.py"
        cmd = [
            sys.executable, str(orchestrator),
            "--channel", channel,
            "--topic",   topic,
        ]
        if mode == "editing":
            cmd.extend(["--mode", "editing"])
        return cmd


# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="SEOWON-AUTO ENGINE 통합 진입점",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python master.py run    --channel jusi     --topic "시니어 조언"
  python master.py queue  --channel unspoken --topic "비 오는 새벽" --priority 7
  python master.py batch
  python master.py sync
  python master.py status
""")
    sub = parser.add_subparsers(dest="command", required=True)

    # run
    p_run = sub.add_parser("run", help="단일 작업 즉시 실행")
    p_run.add_argument("--channel", required=True)
    p_run.add_argument("--topic",   required=True)
    p_run.add_argument("--mode",    default="synthesis", choices=["synthesis", "editing"])
    p_run.add_argument("--no-sync",     action="store_true")
    p_run.add_argument("--no-notify",   action="store_true")

    # queue
    p_q = sub.add_parser("queue", help="배치 큐에 추가")
    p_q.add_argument("--channel",  required=True)
    p_q.add_argument("--topic",    required=True)
    p_q.add_argument("--mode",     default="synthesis", choices=["synthesis", "editing"])
    p_q.add_argument("--priority", type=int, default=5)

    # batch
    p_b = sub.add_parser("batch", help="야간 배치 실행")
    p_b.add_argument("--no-sync",   action="store_true")
    p_b.add_argument("--no-notify", action="store_true")

    # sync / status
    sub.add_parser("sync",   help="GitHub 동기화만")
    sub.add_parser("status", help="현재 상태 출력")

    args = parser.parse_args()
    master = SeowonMaster()

    if args.command == "run":
        master.run(args.channel, args.topic, args.mode,
                   auto_sync=not args.no_sync,
                   notify=not args.no_notify)
    elif args.command == "queue":
        master.queue(args.channel, args.topic, args.mode, args.priority)
    elif args.command == "batch":
        master.run_batch(auto_sync=not args.no_sync,
                         notify=not args.no_notify)
    elif args.command == "sync":
        master.sync_only()
    elif args.command == "status":
        master.status()


if __name__ == "__main__":
    main()
