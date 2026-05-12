"""
notifier.py — Slack/Telegram 멀티 채널 알림
==============================================
배치 완료, 에러 발생, 작업 시작/종료 등 주요 이벤트를 알림.
외부 SDK 없이 webhook URL과 urllib으로 직접 호출.

지원 채널:
  - Slack Webhook (URL 환경변수: SLACK_WEBHOOK)
  - Telegram Bot (BOT_TOKEN, CHAT_ID 환경변수)
  - 콘솔 (항상 출력)

외부 의존성: ZERO (urllib stdlib)
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime


class Notifier:
    """멀티 채널 알림"""

    def __init__(self,
                 slack_webhook: str = None,
                 telegram_token: str = None,
                 telegram_chat_id: str = None):
        self.slack_webhook    = slack_webhook    or os.environ.get("SLACK_WEBHOOK", "")
        self.telegram_token   = telegram_token   or os.environ.get("TELEGRAM_BOT_TOKEN", "")
        self.telegram_chat_id = telegram_chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")

    # ── Slack ────────────────────────────────────────────────────────────────
    def slack(self, text: str, title: str = None) -> bool:
        if not self.slack_webhook:
            return False
        body = {"text": f"*{title}*\n{text}" if title else text}
        return self._post(self.slack_webhook, body)

    # ── Telegram ─────────────────────────────────────────────────────────────
    def telegram(self, text: str, parse_mode: str = "Markdown") -> bool:
        if not (self.telegram_token and self.telegram_chat_id):
            return False
        url  = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        body = {
            "chat_id": self.telegram_chat_id,
            "text":    text,
            "parse_mode": parse_mode,
        }
        return self._post(url, body)

    # ── 통합 알림 ────────────────────────────────────────────────────────────
    def notify(self, text: str, title: str = None, level: str = "info"):
        """모든 활성 채널에 동시 발송"""
        # 콘솔 (항상)
        icon = {"info": "ℹ️", "ok": "✅", "warn": "⚠️", "error": "❌"}.get(level, "📢")
        ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{icon} [{ts}] {title or ''}")
        print(f"   {text}\n")

        # 외부 채널
        if self.slack_webhook:
            self.slack(text, title)
        if self.telegram_token and self.telegram_chat_id:
            full = f"*{title}*\n{text}" if title else text
            self.telegram(full)

    # ── 배치 완료 리포트 ─────────────────────────────────────────────────────
    def batch_completed(self, total: int, done: int, failed: int,
                        elapsed_min: float, output_dir: str = None):
        """배치 작업 완료 리포트"""
        success_rate = (done / total * 100) if total else 0
        emoji = "🎉" if failed == 0 else ("⚠️" if success_rate >= 80 else "❌")

        text = f"""{emoji} 야간 배치 완료
━━━━━━━━━━━━━━━━━━━
✅ 성공:   {done}개
❌ 실패:   {failed}개
📊 성공률: {success_rate:.0f}%
⏱️ 소요:   {elapsed_min:.1f}분
"""
        if output_dir:
            text += f"📁 출력:   {output_dir}\n"

        self.notify(text, title="🌅 SEOWON BATCH COMPLETE",
                    level="ok" if failed == 0 else "warn")

    # ── 작업 시작 ────────────────────────────────────────────────────────────
    def job_started(self, job_id: str, channel: str, topic: str):
        self.notify(
            f"📺 {channel}: {topic}\n🆔 {job_id}",
            title="▶ 작업 시작",
            level="info"
        )

    # ── 작업 완료 ────────────────────────────────────────────────────────────
    def job_done(self, job_id: str, channel: str, topic: str, output_path: str):
        self.notify(
            f"📺 {channel}: {topic}\n📁 {output_path}\n🆔 {job_id}",
            title="✅ 작업 완료",
            level="ok"
        )

    # ── 에러 ─────────────────────────────────────────────────────────────────
    def error(self, message: str, context: str = None):
        text = message
        if context:
            text += f"\n\n📋 컨텍스트:\n{context}"
        self.notify(text, title="❌ 에러 발생", level="error")

    # ── HTTP POST 헬퍼 ───────────────────────────────────────────────────────
    def _post(self, url: str, body: dict) -> bool:
        try:
            data = json.dumps(body).encode("utf-8")
            req  = urllib.request.Request(
                url,
                data=data,
                method="POST",
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status < 300
        except Exception as e:
            print(f"  ⚠️  알림 발송 실패: {e}", file=sys.stderr)
            return False


# ── CLI 테스트 ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="SEOWON Notifier 테스트")
    p.add_argument("text", help="알림 메시지")
    p.add_argument("--title", default=None)
    p.add_argument("--level", default="info", choices=["info","ok","warn","error"])
    args = p.parse_args()

    n = Notifier()
    n.notify(args.text, title=args.title, level=args.level)
