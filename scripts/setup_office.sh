#!/bin/bash
# ============================================================
# setup_office.sh — 사무실 Galaxy Book5 Ultra 자동 셋업
# ============================================================
# 한 번 실행으로 SEOWON-AUTO ENGINE 환경 완성
# 3채널 전부 작업 가능 (seowon, jusi, unspoken)
# Intel Arc 140V 환경, WSL2 Ubuntu
# ============================================================

set -e
echo "════════════════════════════════════════════════════════"
echo "  🏢 SEOWON-AUTO ENGINE — 사무실 Galaxy Book5 셋업"
echo "  💻 Intel Arc 140V + WSL2 Ubuntu"
echo "════════════════════════════════════════════════════════"

if [ "$USER" != "seowo" ]; then
    echo "⚠️  현재 사용자: $USER (예상: seowo)"
    read -p "계속 진행? (y/N) " confirm
    [[ "$confirm" != "y" ]] && exit 1
fi

# ── 1. 시스템 패키지 ─────────────────────────────────────────
echo ""
echo "📦 [1/5] 시스템 패키지 설치..."
sudo apt update -qq
sudo apt install -y ffmpeg yt-dlp git python3 python3-pip

# ── 2. GitHub 클론 ───────────────────────────────────────────
echo ""
echo "📥 [2/5] SEOWON-AUTO ENGINE 클론..."
TARGET=~/seowon-auto-engine
if [ -d "$TARGET" ]; then
    cd "$TARGET" && git pull
else
    git clone https://github.com/tianxiawudi1996-eng/seowon-auto-engine.git "$TARGET"
fi
cd "$TARGET"

# ── 3. video-use 스킬 ────────────────────────────────────────
echo ""
echo "🎬 [3/5] video-use 스킬 설치..."
mkdir -p ~/.claude/skills
if [ ! -d ~/.claude/skills/video-use ]; then
    git clone https://github.com/browser-use/video-use ~/.claude/skills/video-use
    cd ~/.claude/skills/video-use && pip3 install -e . --break-system-packages 2>/dev/null || pip3 install -e .
    cd "$TARGET"
fi

# ── 4. 환경 변수 ─────────────────────────────────────────────
echo ""
echo "🔐 [4/5] .env 생성..."
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# ─── SEOWON-AUTO ENGINE 환경 변수 (사무실 Galaxy Book5) ───
GOOGLE_API_KEY=
ELEVENLABS_API_KEY=
SLACK_WEBHOOK=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

SEOWON_DEVICE=office_galaxy_book5
SEOWON_MAX_CONCURRENT=2
FFMPEG_THREADS=8
EOF
fi
grep -q "^.env$" .gitignore || echo ".env" >> .gitignore

# ── 5. 환경 감지 테스트 ──────────────────────────────────────
echo ""
echo "🔍 [5/5] 환경 감지 테스트..."
python3 scripts/env_detector.py info 2>/dev/null || true

# ── 완료 ──────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════"
echo "  ✅ 사무실 셋업 완료! — 3채널 전부 사용 가능"
echo "════════════════════════════════════════════════════════"
echo ""
echo "📋 다음:"
echo "  1. nano $TARGET/.env  → API 키 입력"
echo "  2. python3 master.py run --channel seowon --topic '안전사고'"
echo ""
