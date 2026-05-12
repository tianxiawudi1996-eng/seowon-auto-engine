"""
batch_runner.py — 야간 배치 자동 실행기
==========================================
자기 전에 작업 큐(jobs.json)에 등록 → 야간 동안 자동 실행 → 아침에 결과 확인
집 데스크탑(Xeon 16코어) 활용 최적화.

특징:
  - JSON 큐 기반 (sqlite 불필요)
  - 작업 우선순위 (1~10)
  - 실패 시 자동 재시도 (최대 3회)
  - 동시 작업 제어 (env_detector의 max_concurrent 사용)
  - 진행 상태 실시간 기록
  - 완료 시 Slack 알림 (선택)

외부 의존성: ZERO (stdlib만 사용)
"""

import json
import os
import sys
import time
import subprocess
import threading
import argparse
from pathlib import Path
from datetime import datetime
from queue import PriorityQueue
from concurrent.futures import ThreadPoolExecutor, as_completed


class BatchRunner:
    """야간 배치 자동 실행기"""

    def __init__(self, queue_path: Path, max_workers: int = 4):
        self.queue_path  = Path(queue_path)
        self.max_workers = max_workers
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.queue_path.exists():
            self.queue_path.write_text("[]", encoding="utf-8")

    def load_queue(self) -> list:
        return json.loads(self.queue_path.read_text(encoding="utf-8"))

    def save_queue(self, jobs: list):
        self.queue_path.write_text(
            json.dumps(jobs, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    # ── 큐 관리 ──────────────────────────────────────────────────────────────
    def add(self, job: dict) -> str:
        """작업 추가"""
        job_id = f"job_{int(time.time() * 1000)}"
        job_record = {
            "id":          job_id,
            "priority":    job.get("priority", 5),
            "channel":     job.get("channel"),
            "topic":       job.get("topic"),
            "mode":        job.get("mode", "synthesis"),
            "command":     job.get("command"),
            "status":      "queued",
            "created_at":  datetime.now().isoformat(),
            "started_at":  None,
            "finished_at": None,
            "retries":     0,
            "max_retries": 3,
            "result":      None,
        }
        jobs = self.load_queue()
        jobs.append(job_record)
        self.save_queue(jobs)
        return job_id

    def update(self, job_id: str, **fields):
        """작업 업데이트"""
        jobs = self.load_queue()
        for job in jobs:
            if job["id"] == job_id:
                job.update(fields)
                break
        self.save_queue(jobs)

    def get_queued(self) -> list:
        """대기 중인 작업 (우선순위 순)"""
        jobs = self.load_queue()
        return sorted(
            [j for j in jobs if j["status"] == "queued"],
            key=lambda j: (-j["priority"], j["created_at"])
        )

    # ── 실행 ──────────────────────────────────────────────────────────────────
    def run_job(self, job: dict) -> dict:
        """단일 작업 실행"""
        job_id = job["id"]
        print(f"\n▶ [{job_id}] 시작 — {job.get('channel')}: {job.get('topic', '')[:50]}")
        self.update(job_id, status="running", started_at=datetime.now().isoformat())

        try:
            cmd = job["command"]
            if isinstance(cmd, str):
                cmd = cmd.split()

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1시간 타임아웃
            )
            success = (result.returncode == 0)
            output  = result.stdout[-2000:] if result.stdout else ""
            error   = result.stderr[-1000:] if result.stderr else ""

            if success:
                self.update(
                    job_id,
                    status="done",
                    finished_at=datetime.now().isoformat(),
                    result={"output": output, "returncode": 0},
                )
                print(f"  ✅ [{job_id}] 완료")
                return {"job_id": job_id, "status": "done"}
            else:
                raise RuntimeError(f"Exit code {result.returncode}: {error}")

        except Exception as e:
            print(f"  ❌ [{job_id}] 실패: {str(e)[:200]}")
            retries = job["retries"] + 1
            if retries < job["max_retries"]:
                # 재시도 큐로 복귀
                self.update(
                    job_id,
                    status="queued",
                    retries=retries,
                    result={"error": str(e)},
                )
                print(f"  🔄 [{job_id}] 재시도 {retries}/{job['max_retries']} 예정")
                return {"job_id": job_id, "status": "retry"}
            else:
                self.update(
                    job_id,
                    status="failed",
                    finished_at=datetime.now().isoformat(),
                    result={"error": str(e), "retries": retries},
                )
                return {"job_id": job_id, "status": "failed"}

    def run_all(self):
        """대기 중인 모든 작업 동시 실행 (max_workers 만큼)"""
        queued = self.get_queued()
        if not queued:
            print("📭 대기 중인 작업 없음")
            return

        print(f"\n🌙 야간 배치 시작 — {len(queued)}개 작업, 동시 {self.max_workers}개\n")
        start = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures = [ex.submit(self.run_job, job) for job in queued]
            for future in as_completed(futures):
                future.result()  # 예외는 이미 run_job에서 처리

        elapsed = (time.time() - start) / 60
        print(f"\n🌅 배치 완료 — 총 {elapsed:.1f}분 소요\n")
        self.report()

    # ── 리포트 ────────────────────────────────────────────────────────────────
    def report(self):
        """현재 큐 상태 리포트"""
        jobs = self.load_queue()
        if not jobs:
            print("📭 큐가 비어있습니다.")
            return

        by_status = {}
        for job in jobs:
            by_status.setdefault(job["status"], []).append(job)

        print("═" * 60)
        print(f"  📊 BATCH QUEUE STATUS — {datetime.now():%Y-%m-%d %H:%M}")
        print("═" * 60)
        for status in ["queued", "running", "done", "failed"]:
            jobs_in_status = by_status.get(status, [])
            icon = {"queued": "⏳", "running": "▶", "done": "✅", "failed": "❌"}[status]
            print(f"  {icon} {status.upper():<10} {len(jobs_in_status):>3}개")
            for j in jobs_in_status[:5]:
                print(f"      [{j['id'][-12:]}] {j.get('channel','?'):<10} {str(j.get('topic',''))[:40]}")
        print("═" * 60)

    # ── 정리 ──────────────────────────────────────────────────────────────────
    def cleanup(self, keep_days: int = 7):
        """완료된 작업 N일 이후 자동 정리"""
        jobs = self.load_queue()
        cutoff = datetime.now().timestamp() - (keep_days * 86400)
        kept = []
        for job in jobs:
            if job["status"] in ["queued", "running"]:
                kept.append(job)
                continue
            finished = job.get("finished_at")
            if finished:
                try:
                    ts = datetime.fromisoformat(finished).timestamp()
                    if ts > cutoff:
                        kept.append(job)
                except Exception:
                    kept.append(job)
        self.save_queue(kept)
        print(f"🧹 정리 완료 — {len(jobs) - len(kept)}개 제거, {len(kept)}개 유지")


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = argparse.ArgumentParser(description="SEOWON Batch Runner")
    p.add_argument("command", choices=["add", "run", "status", "cleanup"])
    p.add_argument("--queue",    default="data/batch_queue.json")
    p.add_argument("--workers",  type=int, default=int(os.environ.get("SEOWON_MAX_CONCURRENT", "4")))
    p.add_argument("--channel",  default=None)
    p.add_argument("--topic",    default=None)
    p.add_argument("--mode",     default="synthesis", choices=["synthesis", "editing"])
    p.add_argument("--cmd",      default=None, help="실행 명령어")
    p.add_argument("--priority", type=int, default=5)
    args = p.parse_args()

    runner = BatchRunner(Path(args.queue), max_workers=args.workers)

    if args.command == "add":
        if not args.cmd:
            print("❌ --cmd 필요. 예: --cmd \"python orchestrator.py --channel jusi --topic '...'\"")
            sys.exit(1)
        job_id = runner.add({
            "channel":  args.channel,
            "topic":    args.topic,
            "mode":     args.mode,
            "command":  args.cmd,
            "priority": args.priority,
        })
        print(f"✅ 큐 추가 완료: {job_id}")

    elif args.command == "run":
        runner.run_all()

    elif args.command == "status":
        runner.report()

    elif args.command == "cleanup":
        runner.cleanup()
