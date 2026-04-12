# SEOWON-AUTO ENGINE v1.0 — Claude Code 하네스

> **진입 즉시 자동 로드. 모든 에이전트는 이 규칙을 준수한다.**

---

## 🎯 시스템 정의

**프로젝트명**: SEOWON-AUTO ENGINE v1.0
**목적**: "영상 만들어줘" 한마디로 기획→대본→편집→업로드 완전 자동화
**운영**: (주)서원토건 미래전략TF / 김무빈 차장
**철학**: 레퍼런스 분석 50% → 대본·리소스 40% → 편집·업로드 10%

---

## 📺 운영 채널 3개

| ID | 채널명 | 컨셉 | 톤 | TTS |
|----|--------|------|-----|-----|
| `seowon` | 서원토건 공식 | 안전교육·현장실무·법령정보 | 전문적·권위있음 | XTTS 남성 |
| `jusi` | 쥬시톡 (JusiTalk) | 시니어 경험 → 주니어 전수 | 친근한 시니어 | XTTS 남성 |
| `unspoken` | 말하지 않는 것들 | 감성 AI 음악 플레이리스트 | 무드·감성 | Suno AI |

---

## 🤖 10에이전트 구조

```
Wave 1 (병렬):
  [Agent-0] SCOUT       → 레퍼런스 수집·성공패턴 분석
  [Agent-1] STRATEGIST  → 컨셉·타겟·훅 전략 수립

Wave 2 (병렬):
  [Agent-2] RESEARCHER  → 팩트체크·신뢰성 검증
  [Agent-3] SCRIPTWRITER→ 채널별 특화 대본 작성
  [Agent-4] VISUAL      → 씬별 이미지 프롬프트 생성

Wave 3 (병렬):
  [Agent-5] TTS         → XTTS v2 음성 생성
  [Agent-6] SUBTITLE    → SRT 자막 생성

Wave 4 (순차):
  [Agent-7] EDITOR      → CapCutAPI JSON 자동 생성
  [Agent-8] QA          → 26개 체크리스트 검수
  [Agent-9] PUBLISHER   → YouTube API 업로드 + SEO
```

---

## 📁 데이터 흐름 (MD 파일 체인)

```
request.md
  → [SCOUT]     → concept.md
  → [STRATEGY]  → strategy.md
  → [SCRIPT]    → script.md
  → [VISUAL]    → scenes.md (이미지 프롬프트)
  → [TTS]       → workspace/audio/voice_N.mp3
  → [SUBTITLE]  → workspace/subtitle.srt
  → [EDITOR]    → output/capcut_projects/{프로젝트명}/
  → [QA]        → output/qa_report.json
  → [PUBLISHER] → output/youtube_queue/{영상ID}.json
```

---

## 🔒 절대 규칙

1. 스키마 위반 금지 — harness/schemas/ JSON 스키마 준수
2. 채널 혼용 금지 — seowon/jusi/unspoken 톤·스타일 절대 혼용 불가
3. 게이트 우회 금지 — QA 통과 없이 PUBLISHER 실행 불가
4. 파일 충돌 금지 — 동일 파일 동시 편집 금지
5. 출력 경로 준수 — 모든 결과물은 output/ 하위에만 저장

---

## ⚡ 실행 명령

```bash
# 영상 생성 시작
/auto-video --channel seowon --topic "안전사고 유형 및 대처방법"
/auto-video --channel jusi   --topic "시니어가 절대 안 알려주는 것들"
/auto-video --channel unspoken --action benchmark

# 레퍼런스만 수집
/scout --channel seowon --topic "건설 안전"

# QA만 실행
/qa-check --project output/capcut_projects/latest/
```
