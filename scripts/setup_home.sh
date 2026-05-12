#!/bin/bash
# ============================================================
# setup_home.sh — 집 Xeon 데스크탑 자동 셋업
# ============================================================
# 한 번 실행으로 SEOWON-AUTO ENGINE 환경 완성
# Xeon E5-2683v4 (16코어) + GTX 960 2GB 최적화
# 개인 채널 전용: 쥬시톡, 말하지않는것들
# 회사 채널(서원토건) 사용 시 권한 차단됨
# ============================================================

set -e
echo "════════════════════════════════════════════════════════"
echo "  🏠 SEOWON-AUTO ENGINE — 집 데스크탑 자동 셋업"
echo "  💻 Xeon E5-2683v4 (16코어) 최적화"
echo "════════════════════════════════════════════════════════"

# ── 0. 사용자 확인 ───────────────────────────────────────────
if [ "$USER" != "ddedi" ]; then
    echo "⚠️  현재 사용자: $USER (예상: ddedi)"
    read -p "계속 진행? (y/N) " confirm
    [[ "$confirm" != "y" ]] && exit 1
fi

# ── 1. 시스템 패키지 ─────────────────────────────────────────
echo ""
echo "📦 [1/6] 시스템 패키지 설치..."
sudo apt update -qq
sudo apt install -y ffmpeg yt-dlp git python3 python3-pip
echo "  ✅ ffmpeg, yt-dlp, git, python3 완료"

# ── 2. GitHub 클론 ───────────────────────────────────────────
echo ""
echo "📥 [2/6] SEOWON-AUTO ENGINE 클론..."
TARGET=~/seowon-auto-engine
if [ -d "$TARGET" ]; then
    echo "  ℹ️  이미 존재함 — pull 진행"
    cd "$TARGET" && git pull
else
    git clone https://github.com/tianxiawudi1996-eng/seowon-auto-engine.git "$TARGET"
fi
cd "$TARGET"
echo "  ✅ 클론 완료: $TARGET"

# ── 3. video-use 스킬 설치 ───────────────────────────────────
echo ""
echo "🎬 [3/6] video-use 스킬 설치..."
mkdir -p ~/.claude/skills
if [ ! -d ~/.claude/skills/video-use ]; then
    git clone https://github.com/browser-use/video-use ~/.claude/skills/video-use
    cd ~/.claude/skills/video-use
    pip3 install -e . --break-system-packages 2>/dev/null || pip3 install -e .
    cd "$TARGET"
fi
echo "  ✅ video-use 설치 완료"

# ── 4. 환경 변수 파일 (.env) ─────────────────────────────────
echo ""
echo "🔐 [4/6] 환경 변수 파일 생성..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# ─── SEOWON-AUTO ENGINE 환경 변수 (집 데스크탑) ───
# 절대 GitHub에 push되지 않음 (.gitignore에 포함)

# AI 엔진
GOOGLE_API_KEY=                        # https://aistudio.google.com/app/apikey

# 영상 편집 (선택)
ELEVENLABS_API_KEY=                    # https://elevenlabs.io/app/settings/api-keys

# 알림 (선택)
SLACK_WEBHOOK=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# 시스템
SEOWON_DEVICE=home_xeon_desktop
SEOWON_MAX_CONCURRENT=4
FFMPEG_THREADS=16
EOF
    echo "  ✅ .env 생성 — 키 채워 넣으세요: nano .env"
else
    echo "  ℹ️  .env 이미 존재 — 유지"
fi

# .gitignore 확인
if ! grep -q "^.env$" .gitignore 2>/dev/null; then
    echo ".env" >> .gitignore
fi

# ── 5. cron 야간 배치 (선택) ─────────────────────────────────
echo ""
echo "🌙 [5/6] 야간 배치 자동화 (cron)..."
CRON_LINE="0 2 * * * cd $TARGET && /usr/bin/python3 scripts/master.py batch >> $TARGET/logs/cron.log 2>&1"
mkdir -p logs
if ! (crontab -l 2>/dev/null | grep -q "master.py batch"); then
    read -p "  매일 새벽 2시 자동 배치 실행 등록? (y/N) " yn
    if [[ "$yn" == "y" ]]; then
        (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
        echo "  ✅ cron 등록 — 매일 02:00 자동 실행"
    fi
fi

# ── 6. 환경 감지 테스트 ──────────────────────────────────────
echo ""
echo "🔍 [6/6] 환경 감지 테스트..."
python3 scripts/env_detector.py info 2>/dev/null || echo "  ⚠️  추후 master.py 실행 시 동작 확인"

# ── 완료 ──────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅ 집 데스크탑 셋업 완료!"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📋 다음 단계:"
echo "  1. nano $TARGET/.env  → API 키 입력"
echo "  2. python3 master.py status"
echo "  3. python3 master.py queue --channel jusi --topic '주제'"
echo "  4. python3 master.py batch  (또는 새벽 2시 자동 실행)"
echo ""
echo "⛔ 차단된 채널: seowon (서원토건은 사무실에서만)"
echo "✅ 사용 가능:    jusi, unspoken"
echo ""
