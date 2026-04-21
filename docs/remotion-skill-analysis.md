# 🎬 Remotion Skill × SEOWON-AUTO ENGINE 적용 분석

> 작성: 2026.04.21 | 참조: https://youtu.be/_7orn3F9NHQ
> 핵심: Claude Code + Remotion = 코드로 MP4 직접 생성 (CapCut 불필요)

---

## 1. Remotion Skill이란?

**한 줄 정의**: Claude Code가 React 컴포넌트를 작성 → Remotion이 MP4로 렌더링

```
기존 파이프라인:
  Claude → 대본 → CapCut JSON → CapCut 앱에서 열기 → MP4 수동 내보내기

새 파이프라인:
  Claude → 대본 → Remotion React 컴포넌트 → npx remotion render → MP4 완성 ✅
```

### 핵심 원리
- 영상의 각 프레임 = React 컴포넌트
- 시간 = `useCurrentFrame()` 훅으로 제어
- 애니메이션 = `interpolate()`, `spring()` 함수
- 렌더링 = headless 브라우저가 프레임별 캡처

### 설치 (한 줄)
```bash
npx skills add remotion-dev/skills
```
또는 Claude Code → Customize → Skills → "remotion" 검색 → 토글 ON

---

## 2. SEOWON-AUTO ENGINE 적용 포인트

### 기존 vs 신규 비교

| 단계 | 기존 (CapCut JSON) | 신규 (Remotion Skill) |
|------|-------------------|----------------------|
| 편집 방식 | JSON 파일 생성 → CapCut 수동 열기 | React 코드 → 자동 MP4 렌더 |
| 자동화 수준 | 반자동 (CapCut 실행 필요) | 완전 자동 (CLI 렌더) |
| 의존성 | CapCut 앱 설치 필요 | Node.js + ffmpeg만 |
| 커스텀 수준 | JSON 스키마 제한 | React 무제한 |
| 배치 생성 | 불가 | JSON 데이터로 100편 자동 |

### 채널별 적용 전략

#### 서원토건 (1920×1080 롱폼)
```
- 안전사고 통계 → 애니메이션 차트 (Remotion 데이터 시각화)
- 현장 사진 + 텍스트 오버레이 자동 구성
- 법령 조항 → 타이핑 효과 텍스트 애니메이션
```

#### 쥬시톡 (1080×1920 쇼츠)
```
- 9:16 세로형 자동 설정
- 말풍선 등장 애니메이션
- 시니어 조언 카드 슬라이드 효과
```

#### 말하지 않는 것들 (플레이리스트)
```
- 감성 배경 + 가사/트랙명 fade-in
- 앨범 아트 켄번스 효과
- 트랙 전환 디졸브 자동화
```

---

## 3. 즉시 적용 가능한 Remotion 프롬프트

### 서원토건 첫 영상용
```
Use the Remotion best practices skill.

Create a YouTube video (1920×1080, 30fps, 5 minutes) about
"건설현장 안전사고 유형 및 대처방법"

Structure:
- Intro (10s): 서원토건 로고 + 제목 fade-in
- Scene 1-7 (각 40s): 안전사고 유형별 설명
  - 배경: 어두운 네이비 (#003087)
  - 텍스트: 흰색, NanumGothic
  - 통계 수치: 카운트업 애니메이션
- Outro (10s): 구독/좋아요 CTA

SAFE ZONE: 상하 80px, 좌우 60px
FONT: 최소 36px
```

### 쥬시톡 쇼츠용
```
Use the Remotion best practices skill.

Create a YouTube Short (1080×1920, 30fps, 60s) about
"시니어가 절대 안 알려주는 직장 생존법"

Style: 말풍선 + 반응형 텍스트 카드
Color: #E85D26 accent
```

---

## 4. 설치 및 통합 순서

```bash
# Step 1: Node.js + ffmpeg 확인
node --version  # 18+ 필요
ffmpeg -version

# Step 2: Remotion 프로젝트 생성
npx create-video@latest seowon-videos
cd seowon-videos

# Step 3: Remotion Skill 설치
npx skills add remotion-dev/skills

# Step 4: Claude Code 실행
claude
# → "Use the Remotion best practices skill. 영상 설명..."

# Step 5: 렌더링
npx remotion render src/Video.tsx MyVideo output/video.mp4
```

---

## 5. SEOWON-AUTO ENGINE v3.0 업그레이드 계획

```
현재 v2.0:
  Gemini API → 대본 → CapCut JSON → (수동) → MP4

목표 v3.0:
  Gemini API → 대본 → Remotion 컴포넌트 → MP4 자동 렌더 → YouTube 업로드
                                              ↑
                                    완전 자동화 달성!
```

### 추가할 파일
- `src/remotion_builder.py` — Remotion 컴포넌트 자동 생성
- `remotion/compositions/SeowonVideo.tsx` — 서원토건 템플릿
- `remotion/compositions/JusiShort.tsx` — 쥬시톡 쇼츠 템플릿
- `remotion/compositions/UnspokenPlaylist.tsx` — 감성 플레이리스트 템플릿

---

## 6. 핵심 수치

- Remotion Skill 주간 설치: **117,000회**
- 런치 데모 조회수: **6M+**
- 30초 데이터 시각화 영상 제작: **30~45분** (렌더 포함)
- 50개 영상 배치 생성: **15분**
- 기존 모션그래픽 스튜디오 견적 대비: **비용 ~0원**

