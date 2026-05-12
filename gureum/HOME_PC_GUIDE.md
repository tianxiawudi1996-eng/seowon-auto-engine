# 🐾 구름이 뮤직비디오 자동 생성 — 집 PC 실행 가이드

> 위치: `D:\멍냥구조대\김정원대표님`
> 기존 작업 이어서 완성하기

---

## 🚀 30초 안에 시작 — 한 줄 실행

### 방법 1: Claude Code로 자동 진행 (추천)

집 PC에서 WSL2 Ubuntu 또는 PowerShell 열고:

```bash
# 1. 작업 폴더로 이동
cd "D:/멍냥구조대/김정원대표님"
# 또는 WSL2: cd "/mnt/d/멍냥구조대/김정원대표님"

# 2. Claude Code 실행
claude

# 3. 아래 프롬프트 복사 붙여넣기
```

### 🎯 Claude Code 프롬프트 (복붙용)

```
이 폴더(D:\멍냥구조대\김정원대표님)에 있는 모든 자료(영상·이미지·음원)를 
활용해서 구름이 뮤직비디오를 자동 완성해줘.

요구사항:
- 출력: 1920x1080, 30fps MP4
- 9개 씬 순서 (에그타르트→풀→소주→커플→말차→유모차→볼찌→우비→장미)
- 인트로 "구름이의 하루 🐾" 텍스트 페이드인
- 아웃트로 "Music Video by 김무빈" 
- 켄번스 효과 + 자연스러운 페이드 트랜지션
- 색보정: warm cinematic
- 음원 자동 감지 후 합성

먼저 폴더를 스캔해서 어떤 파일이 있는지 보여주고,
편집 계획을 알려준 후 진행해줘.

ffmpeg 사용 가능. Python stdlib만 사용.
최종 출력: ./gureum_output/final_gureum_mv.mp4
```

---

### 방법 2: 자동화 스크립트 직접 실행

```bash
# 1. 스크립트 다운로드
cd "D:/멍냥구조대/김정원대표님"
curl -O https://raw.githubusercontent.com/tianxiawudi1996-eng/seowon-auto-engine/main/gureum/gureum_mv_builder.py

# 2. 스캔만 먼저
python gureum_mv_builder.py --scan-only

# 3. 결과 확인 후 본격 실행
python gureum_mv_builder.py
```

---

## 📋 사전 체크리스트

### ✅ 필수
- [ ] **ffmpeg 설치 확인** — `ffmpeg -version` 실행해서 버전 나오면 OK
- [ ] **Python 3.8+** — `python --version`
- [ ] **D:\멍냥구조대\김정원대표님** 폴더 존재 확인

### ffmpeg 설치 (없을 때)

**Windows (PowerShell 관리자):**
```powershell
# Chocolatey 사용
choco install ffmpeg

# 또는 winget
winget install Gyan.FFmpeg

# 또는 수동 다운로드
# https://www.gyan.dev/ffmpeg/builds/
# → ffmpeg-release-essentials.zip 다운
# → C:\ffmpeg 압축 해제
# → 시스템 환경변수 PATH에 C:\ffmpeg\bin 추가
```

**WSL2 Ubuntu:**
```bash
sudo apt update && sudo apt install ffmpeg -y
```

---

## 🎬 자동 처리되는 작업 9가지

1. **폴더 재귀 스캔** — 모든 mp4/mov/jpg/png/mp3 자동 발견
2. **파일명 기반 씬 분류** — "에그타르트", "풀", "소주" 등 키워드로 자동 매칭
3. **음원 자동 감지** — 가장 긴 mp3/wav를 BGM으로 선택
4. **이미지 → 영상 변환** — 켄번스 효과 (미세 줌)
5. **영상 트림 & 리사이즈** — 1920×1080 16:9 통일
6. **색보정 자동 적용** — Warm cinematic
7. **씬 합치기** — 9개 씬 순서대로 연결
8. **음원 합성** — 영상 길이에 맞춰 자동 조정
9. **인트로/아웃트로 텍스트** — 페이드인 자막

---

## 📁 출력 결과

```
./gureum_output/
├── final_gureum_mv.mp4          ⭐ 최종 결과물
├── scan_result.json             📋 스캔 보고서
└── _work/                       🛠️ 작업 폴더 (씬별 클립)
    ├── clip_00_egg_tart.mp4
    ├── clip_01_pool.mp4
    ├── clip_02_soju.mp4
    └── ...
```

---

## 🔧 자주 묻는 것

**Q. 파일 분류가 안 됐어요**
→ 파일명에 "에그타르트", "풀", "소주" 같은 한글 키워드가 있어야 자동 분류됩니다.
→ 수동으로 폴더 안에 `01_egg_tart.jpg` 식으로 이름 바꿔주면 더 정확합니다.

**Q. 음원이 영상보다 길어요**
→ `--shortest` 옵션이 자동 적용되어 영상 길이에 맞춰집니다.
→ 음원에 맞추고 싶으면 씬 개수를 늘리세요.

**Q. 더 길게 만들고 싶어요**
→ `GUREUM_CONFIG["scene_max_duration"]` 을 8 → 12로 변경

**Q. 픽사 스타일 변환은?**
→ 이건 영상 편집만 자동화. 픽사 변환은 Kling AI / Runway에서 진행 후 결과물을 폴더에 넣으면 자동 인식됩니다.

---

## 🎯 다음 단계 (영상 완성 후)

1. **YouTube 업로드 메타데이터** — 이전 작업분 그대로 사용
2. **썸네일 제작** — "실제 vs 픽사" 비교 구도
3. **쇼츠 추가 생성** — 우비 씬 or 볼찌 씬 15초 클립

---

## 💛 이전 작업 자산 (재활용)

- ✅ 9개 씬 픽사 프롬프트 (Kling/Runway용)
- ✅ 유튜브 제목 A/B 안
- ✅ 썸네일 컨셉
- ✅ 영상 설명문 + 태그
- ✅ 챕터 타임스탬프

> 노션 대화 기록에 모두 저장되어 있음 (2026.04.11 작업)
