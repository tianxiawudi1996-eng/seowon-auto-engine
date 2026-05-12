# 🎬 SEOWON-AUTO ENGINE v3.0 — Video-Use 통합 설계

> 작성: 2026.04.21 | 참조: https://www.youtube.com/live/hyuLNOva8dk
> 핵심 발견: `browser-use/video-use` 스킬 (★5.6k, 조코딩님 라이브 데모)

---

## 🚨 패러다임 전환: 두 가지 영상 생성 방식 통합

이전까지 우리 시스템은 "**처음부터 만들기 (Synthesis)**" 방식만 다뤘다.
이제 "**촬영본 자동 편집 (Editing)**" 방식이 추가된다.

### v2.0 vs v3.0

| 구분 | v2.0 (Synthesis) | v3.0 (Editing) — NEW |
|------|------------------|---------------------|
| 입력 | 주제 (텍스트) | 촬영 영상 파일 (mp4) |
| 처리 | 이미지+TTS+자막 합성 | 영상 분석 + 자동 컷편집 |
| 출력 | CapCut JSON | final.mp4 완성본 |
| 적합 채널 | 쥬시톡·말하지않는것들 | **서원토건 (현장 영상)** |
| 도구 | capcut_builder.py | video-use 스킬 |

---

## 📦 video-use 스킬 분석

GitHub: https://github.com/browser-use/video-use (★5.6k)

### 핵심 기능 9가지

1. **Filler word 자동 제거** — "음...", "어..." 같은 군더더기 컷
2. **데드 스페이스 제거** — 테이크 사이 침묵 컷
3. **자동 색보정** — Warm cinematic / Neutral punch / 커스텀
4. **30ms 오디오 페이드** — 컷 지점마다 "팝" 소리 방지
5. **자막 자동 번인** — 기본 2단어 대문자 청크
6. **애니메이션 오버레이** — Manim, Remotion, PIL 병렬 sub-agent로 생성
7. **자체 검수** — 컷 경계마다 결과물 자가 평가
8. **세션 메모리** — `project.md`에 다음 작업 이어가기
9. **트랜스크립트 기반** — ElevenLabs Scribe로 단어 단위 정확도

### 작동 원리 (LLM은 영상을 "본다"가 아니라 "읽는다")

```
Layer 1: 오디오 트랜스크립트 (필수)
  ElevenLabs Scribe → 단어 단위 타임스탬프 + 화자 구분 + 효과음 감지

Layer 2: 비주얼 (필요 시)
  ffmpeg 프레임 추출 → Claude가 이미지로 분석
```

---

## 🏗️ SEOWON-AUTO ENGINE v3.0 통합 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│           SEOWON-AUTO ENGINE v3.0 — 듀얼 모드               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [MODE A: Synthesis] — 처음부터 영상 만들기                  │
│    ├─ Gemini API → 대본 생성                                 │
│    ├─ Imagen/SD → 씬 이미지 생성                             │
│    ├─ XTTS v2 → 음성 합성                                    │
│    └─ capcut_builder.py → draft_content.json                 │
│                                                              │
│  [MODE B: Editing] — 촬영본 자동 편집 (NEW)                  │
│    ├─ ffmpeg → 영상 메타데이터 추출                          │
│    ├─ ElevenLabs Scribe → 트랜스크립트                       │
│    ├─ Claude (video-use) → 컷 결정 + 자막                    │
│    ├─ Manim/Remotion → 애니메이션 오버레이                   │
│    └─ ffmpeg → final.mp4 렌더                                │
│                                                              │
│  [공통 다운스트림]                                            │
│    ├─ QA 검수 (26개 체크리스트)                              │
│    └─ YouTube API 자동 업로드                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 채널별 최적 모드 매칭

| 채널 | 추천 모드 | 이유 |
|------|---------|------|
| 서원토건 | **MODE B (편집)** | 현장 인터뷰·안전교육 촬영본 자동편집이 핵심 |
| 쥬시톡 | A 또는 B | 시니어 토크 촬영(B) 또는 카드뉴스 합성(A) |
| 말하지않는것들 | **MODE A (합성)** | 음악+이미지 합성형 플레이리스트 |

---

## 🛠️ 설치 명령

### Galaxy Book5 Ultra (WSL2 Ubuntu) 기준

```bash
# 1. video-use 클론
git clone https://github.com/browser-use/video-use ~/.claude/skills/video-use

# 2. 의존성
cd ~/.claude/skills/video-use
pip install -e .         # 또는 uv sync

# 3. ffmpeg 설치
sudo apt install ffmpeg yt-dlp

# 4. ElevenLabs API 키 설정
cp .env.example .env
echo "ELEVENLABS_API_KEY=your_key" >> .env

# 5. Claude Code에서 스킬 활성화
claude
> /skills list                  # 활성화된 스킬 확인
> /skills enable video-use      # video-use 활성화
```

ElevenLabs API 키: https://elevenlabs.io/app/settings/api-keys

---

## 🚀 실전 워크플로우 예시

### 서원토건: 현장 안전교육 영상 자동 편집

```bash
# 1. 촬영본 폴더 준비
mkdir -p ~/videos/seowon-safety-001
# (현장에서 찍은 raw 영상들 복사)

# 2. Claude Code 실행
cd ~/videos/seowon-safety-001
claude

# 3. 자연어 명령
> 이 폴더의 영상들로 5분짜리 안전교육 영상을 만들어줘.
> 채널: 서원토건 (1920x1080)
> 필러 워드 제거, 한영 자막, warm cinematic 색보정.
> 자막 위치는 하단 88%, 폰트는 NanumGothicBold 36pt.

# 4. AI 자동 작업
- 모든 영상 트랜스크립트화 (ElevenLabs)
- 최적 컷 순서 결정
- 자막 생성 + 번인
- 색보정 적용
- final.mp4 출력
```

### 쥬시톡: 시니어 토크 1시간 → 쇼츠 5개 자동 분할

```bash
cd ~/videos/jusi-talk-001
claude

> 이 1시간 토크 영상에서 가장 인상적인 5개 구간을 찾아서
> 각각 60초 세로 쇼츠로 만들어줘.
> 9:16 크롭, 자막 2단어 대문자 청크.
```

---

## 💡 핵심 통합 포인트

### 1. video-use × Gemini API 결합
video-use는 기본적으로 Claude API를 쓰지만, 우리는 Gemini로 대체 가능.
ElevenLabs는 Scribe(트랜스크립트)만 쓰므로 비용 매우 저렴.

### 2. SEOWON 워크플로우 통합
```python
# src/orchestrator.py 에 모드 추가
class Orchestrator:
    def run(self, mode: str, channel: str, ...):
        if mode == "synthesis":
            # 기존 v2.0 파이프라인
            self._run_synthesis(channel, topic)
        elif mode == "editing":
            # video-use 스킬 호출
            self._run_video_use(channel, source_folder)
```

### 3. 비용 비교

| 항목 | 비용 |
|------|------|
| ElevenLabs Scribe | $0.40/시간 (단어 단위 트랜스크립트) |
| Claude API (편집 결정) | ~$0.10/영상 |
| Manim/Remotion 렌더 | $0 (로컬) |
| **영상 1편당 총** | **~$0.50 (700원)** |

기존 v2.0(이미지 합성, ~5,000원) 대비 **86% 저렴**.

---

## 📊 핵심 수치

- video-use GitHub Star: **5,600개** (2026.04 기준)
- 포크: **777개**
- 조코딩님 라이브 동시 시청: 1,500+ 명
- 1시간 영상 자동 편집 소요: **약 8~15분**
- 영상 1편당 비용: **약 700원** (기존 대비 86% 감소)

---

## ✅ 다음 단계 액션

- [ ] Galaxy Book5에서 `video-use` 스킬 설치
- [ ] ElevenLabs API 키 발급 (https://elevenlabs.io)
- [ ] 서원토건 현장 영상 테스트 촬영 1편
- [ ] `src/video_use_runner.py` 작성 (orchestrator 통합)
- [ ] 듀얼 모드 CLI 확장: `--mode synthesis|editing`
- [ ] 비용 트래커 추가 (편당 ElevenLabs 사용량 기록)
- [ ] GitHub 푸시 + 노션 업데이트

---

## 🔗 참고 자원

- video-use: https://github.com/browser-use/video-use
- 조코딩 라이브: https://www.youtube.com/live/hyuLNOva8dk
- ElevenLabs Scribe: https://elevenlabs.io/scribe
- SEOWON-AUTO ENGINE: https://github.com/tianxiawudi1996-eng/seowon-auto-engine
