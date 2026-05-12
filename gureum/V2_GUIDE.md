# 🐾 구름이 뮤직비디오 v2 — 풀스택 영화급 자동 생성

> v1과 차이: **3가지 동시 출력** (자동 영상 + CapCut JSON + Remotion 컴포넌트)
> 영화급 색보정, 씬별 다른 무드, 자막 페이드인/아웃 자동

---

## 🎯 v1 vs v2 차이

| 항목 | v1 (단순) | v2 (풀스택) |
|------|---------|-----------|
| 영상 출력 | 1개 (ffmpeg) | **1개 (영화급)** |
| CapCut JSON | ❌ | **✅ 자동 생성** |
| Remotion 컴포넌트 | ❌ | **✅ 자동 생성** |
| 픽사 변환본 인식 | ❌ | **✅ 자동 우선 사용** |
| 씬별 색보정 | 1종 | **9종 (씬마다 다른 무드)** |
| 켄번스 효과 | 1종 | **7종 (zoom in/out, pan, macro 등)** |
| 자막 페이드 | ❌ | **✅ 인/아웃 자동** |
| 첫/마지막 페이드 | ❌ | **✅ 영화처럼** |
| 음원 페이드 | ❌ | **✅ 자동** |
| CapCut 자동 등록 | ❌ | **✅ %LOCALAPPDATA% 자동 복사** |

---

## 🚀 집 PC에서 한 줄 실행

### Cowork에 붙여넣을 프롬프트

```
구름이 뮤직비디오 풀스택 v2를 진행해줘.

[자료 위치]
D:\멍냥구조대\김정원대표님

[스크립트]
GitHub: https://github.com/tianxiawudi1996-eng/seowon-auto-engine/blob/main/gureum/gureum_mv_v2_fullstack.py
이 파일을 다운로드해서 실행해줘.

[순서]
1. 폴더 스캔 (--scan-only 먼저)
2. 픽사 변환본 우선 사용, 없으면 실사
3. 영화급 자동 영상 생성
4. CapCut JSON 동시 출력 (자동 등록까지)
5. Remotion 인트로/아웃트로 컴포넌트 생성

[출력]
./gureum_output_v2/
├── final_gureum_mv.mp4         ⭐ 자동 완성품
├── capcut_project/              📝 CapCut 후작업용
├── remotion_intro_outro/        🎬 Remotion 컴포넌트
└── project.md                   📋 작업 메모리

ffmpeg 필요. Python stdlib만 사용.
```

---

## 📊 9개 씬 × 9가지 무드 (자동 적용)

| 씬 | 무드 | 색보정 | 켄번스 |
|------|------|------|--------|
| 🥧 에그타르트 | warm_curiosity | Warm cinematic | Zoom in |
| 🌊 수영장 | summer_vibrant | Vibrant teal | Pan right |
| 🍶 소주병 | moody_warm | Moody amber | Rack focus |
| 👫 커플 산책 | soft_romantic | Soft pastel | Slow pan |
| 🍵 말차 케이크 | calm_green | Matcha tone | Zoom out |
| 🛺 유모차 | cozy_warm | Warm cinematic | Side pan |
| 🤍 볼찌 | soft_focus | Soft pastel | Macro zoom |
| 🌧️ 우비 | playful_cool | Cool blue | Zoom in |
| 🌹 장미 부케 | emotional_pink | Rose pink | Slow zoom out |

각 씬마다 **자막 페이드인/아웃 자동**:
- 0.5초 페이드인 → 본문 → 0.5초 페이드아웃

---

## 🎬 출력 3가지 사용법

### 1️⃣ 자동 완성 영상 (final_gureum_mv.mp4)
바로 YouTube 업로드 가능. 음원 + 자막 + 색보정 + 트랜지션 다 됨.

### 2️⃣ CapCut JSON (capcut_project/)
- CapCut 열면 **"구름이의 하루" 프로젝트 자동 등장**
- 모든 씬 타임라인에 이미 배치됨
- 자막·색보정·켄번스 다 적용된 상태
- 미세 조정만 하면 됨

### 3️⃣ Remotion 컴포넌트 (remotion_intro_outro/)
```bash
cd remotion_intro_outro
npm install
npm start          # 실시간 미리보기
npm run build-intro   # → intro.mp4
npm run build-outro   # → outro.mp4
```

영화 같은 인트로/아웃트로 추가 가능. 메인 영상과 ffmpeg로 합치면 끝.

---

## 💡 추천 워크플로우

```
1. 자동 영상 (final_gureum_mv.mp4) 먼저 확인
   ↓
   👍 마음에 들면 → YouTube 업로드
   ↓
   🤔 일부 수정 필요 → CapCut 열어서 미세 조정
   ↓
   🎬 더 영화처럼 → Remotion으로 인트로/아웃트로 추가
```

---

## 🔍 픽사 변환본 자동 인식

파일명에 다음 키워드 있으면 픽사 버전으로 인식:
- `pixar`, `kling`, `runway`, `ai_video`, `3d`

예시:
- `01_egg_tart_pixar.mp4` ← 픽사 버전으로 인식
- `01_egg_tart.mp4` ← 실사 버전

**픽사 버전 있으면 우선 사용**, 없으면 실사 사용.

---

## ⚙️ Cowork 자동 처리되는 것

1. 폴더 재귀 스캔 (모든 mp4/jpg/mp3 발견)
2. 픽사 버전 vs 실사 자동 구분
3. 9개 씬 자동 매칭
4. 음원 자동 감지 (가장 긴 파일)
5. 씬별 9가지 무드 자동 적용
6. 자막 페이드인/아웃 자동
7. 영화 인/아웃 페이드
8. 음원 페이드 (2초 인, 3초 아웃)
9. CapCut 드래프트 폴더 자동 등록
10. Remotion 컴포넌트 생성
11. project.md 자동 작성

---

## 📁 GitHub 위치

https://github.com/tianxiawudi1996-eng/seowon-auto-engine/tree/main/gureum
