# 🎬 SEOWON-AUTO ENGINE 마스터 통합 패키지

> 집 ↔ 사무실 양방향 자동화 시스템
> 한 줄 명령으로 환경 감지 + 권한 분리 + 동기화 + 배치 + 알림 처리

---

## 📦 패키지 구성

```
scripts/
├── master.py            ⭐ 모든 작업의 진입점
├── env_detector.py      🔍 환경 자동 감지 + 권한 분리
├── sync_engine.py       🔄 GitHub 양방향 자동 동기화
├── batch_runner.py      🌙 야간 배치 큐 실행기
├── notifier.py          📢 Slack/Telegram 알림
├── setup_home.sh        🏠 집 데스크탑 셋업
└── setup_office.sh      🏢 사무실 노트북 셋업
```

---

## 🚀 30초 시작 가이드

### 집 데스크탑 (Xeon 16코어)

```bash
cd ~
curl -O https://raw.githubusercontent.com/tianxiawudi1996-eng/seowon-auto-engine/main/scripts/setup_home.sh
bash setup_home.sh
nano ~/seowon-auto-engine/.env       # API 키 입력
```

### 사무실 Galaxy Book5

```bash
cd ~
curl -O https://raw.githubusercontent.com/tianxiawudi1996-eng/seowon-auto-engine/main/scripts/setup_office.sh
bash setup_office.sh
nano ~/seowon-auto-engine/.env
```

---

## 🎯 자동화 원칙 4가지

### 1. 환경 자동 감지
사용자명(`ddedi` / `seowo`) 기반으로 어떤 PC인지 자동 인식.
별도 설정 불필요.

```bash
$ python3 master.py status

════════════════════════════════════════════════════
  🎬 SEOWON-AUTO ENGINE v3.0 — 환경 감지
════════════════════════════════════════════════════
  📍 위치:     집
  💻 디바이스: Xeon E5-2683v4 Desktop
  👤 사용자:   ddedi@home-pc
  ✅ 허용 채널: jusi, unspoken
  ⛔ 차단 채널: seowon
  ⚡ ffmpeg 스레드: 16개 (동시 작업 4개)
  🌙 야간 배치: 가능
════════════════════════════════════════════════════
```

### 2. 채널 권한 자동 분리
회사/개인 프로젝트 분리 원칙 자동 강제.

| 환경 | seowon | jusi | unspoken |
|------|--------|------|----------|
| 🏢 사무실 (seowo) | ✅ | ✅ | ✅ |
| 🏠 집 (ddedi) | ⛔ | ✅ | ✅ |
| 📱 모바일 | ⛔ | ✅ | ✅ |

집에서 실수로 서원토건 작업 시도하면 자동 차단.

### 3. GitHub 양방향 자동 동기화
작업 시작 = `git pull` 자동 / 작업 종료 = `git push` 자동.
충돌 시 안전 stash로 자동 백업.

### 4. 야간 배치 자동 실행
자기 전 큐에 작업 등록 → 새벽 2시 자동 실행 → 아침에 결과 알림.

---

## 💡 주요 명령

### 즉시 실행 (단일 영상)
```bash
python3 master.py run --channel jusi --topic "시니어가 절대 안 알려주는 것들"
```
→ 환경 감지 + pull + 영상 생성 + push + 알림 자동

### 배치 큐에 추가 (자기 전)
```bash
python3 master.py queue --channel jusi     --topic "시니어 조언 #1"
python3 master.py queue --channel jusi     --topic "보고서 작성법" --priority 8
python3 master.py queue --channel unspoken --topic "비 오는 새벽"
```

### 야간 배치 실행 (수동)
```bash
python3 master.py batch
```
또는 cron으로 매일 새벽 2시 자동.

### 동기화만
```bash
python3 master.py sync
```

### 현재 상태
```bash
python3 master.py status
```

---

## 🌙 추천 워크플로우

### 평일 (사무실)
```
출근 → python3 master.py sync     # 집에서 한 작업 받아오기
     → 서원토건 영상 작업
     → python3 master.py run --channel seowon --topic "..."
퇴근 → 자동으로 push 완료된 상태
```

### 평일 저녁 (집)
```
귀가 → python3 master.py sync     # 사무실 최신 받기
     → 자기 전: 큐에 작업 등록
     → python3 master.py queue --channel jusi --topic "..."  ×5개
취침 → 새벽 2시 자동 배치 실행 (Xeon 16코어 풀가동)
아침 → Slack/Telegram 알림으로 결과 확인
```

### 휴일 (집)
```
python3 master.py queue --channel unspoken --topic "..." × N
python3 master.py batch  → 한 번에 다 처리
```

---

## 🔐 보안

- `.env` 파일은 절대 GitHub 푸시 안 됨 (`.gitignore` 강제)
- API 키는 환경 변수로만 관리
- 회사/개인 분리 원칙 코드 레벨에서 강제
- 토큰은 git remote URL에 저장 안 함

---

## 📞 알림 설정

### Slack
```bash
echo "SLACK_WEBHOOK=https://hooks.slack.com/services/..." >> .env
```

### Telegram
```bash
echo "TELEGRAM_BOT_TOKEN=..." >> .env
echo "TELEGRAM_CHAT_ID=..." >> .env
```

알림이 가는 이벤트:
- 작업 시작 / 종료 / 실패
- 배치 완료 리포트 (성공/실패 통계)

---

## 🔧 트러블슈팅

**Q. 환경 감지가 잘못됐어요**
→ `env_detector.py`의 `username_match` 수정

**Q. 야간 배치가 안 돌아갔어요**
→ `crontab -l` 확인 / `~/logs/cron.log` 체크

**Q. push 실패해요**
→ `git status` 확인 / 토큰 만료(90일) 체크

**Q. 채널 권한이 너무 빡세요**
→ `env_detector.py` 의 `ENV_PROFILES` 수정 (단, 회사/개인 분리 원칙 유지 권장)

---

## 📊 성능 비교

| 작업 | 사무실 (Galaxy Book5) | 집 (Xeon 16코어) |
|------|--------------------|----------------|
| ffmpeg 인코딩 1편 | ~8분 | ~2분 ⚡ |
| 동시 작업 | 2개 | 4개 ⚡ |
| 야간 5편 배치 | 비추천 | **최적** ⭐ |
| 코딩·테스트 | **최적** ⭐ | 가능 |

**결론**: 사무실은 기획·개발, 집은 인코딩·배치. 분업 최적화.
