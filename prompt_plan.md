# SEOWON-AUTO ENGINE — prompt_plan.md
# Claude Code Agent Teams 실행 계획

## 프로젝트 타입: feature
## 병렬: 3

---

## Wave 1 — 레퍼런스 & 전략 (병렬)

- [ ] Task 1: Scout Agent 실행
  - src/scout_agent.py 의 ScoutAgent 실행
  - 채널별 레퍼런스 분석 → workspace/concept.md 생성
  - 출력: workspace/{session}/concept.md

- [ ] Task 2: Strategy Agent 실행 (depends: Task 1)
  - concept.md 기반 전략 수립
  - 훅·제목·썸네일·씬구성 확정
  - 출력: workspace/{session}/strategy.md

---

## Wave 2 — 대본 & 비주얼 (병렬)

- [ ] Task 3: Script Writer 실행 (depends: Task 2)
  - src/script_agent.py 의 ScriptAgent 실행
  - 채널별 톤 적용 대본 생성
  - 출력: workspace/{session}/script.md + scenes.md

- [ ] Task 4: Visual Prompt 생성 (depends: Task 2)
  - scenes.md 기반 이미지 프롬프트 생성
  - DALL-E / Midjourney 프롬프트 최적화
  - 출력: workspace/{session}/visual_prompts.md

---

## Wave 3 — 음성 & 자막 (병렬)

- [ ] Task 5: TTS 생성 (depends: Task 3)
  - src/tts_agent.py 의 TTSAgent 실행
  - XTTS v2로 씬별 음성 생성
  - 출력: workspace/{session}/audio/voice_N.mp3

- [ ] Task 6: 자막 생성 (depends: Task 3)
  - script.md → SRT 자막 변환
  - 출력: workspace/{session}/subtitle.srt

---

## Wave 4 — 편집 & 검수 & 업로드 (순차)

- [ ] Task 7: CapCut Builder 실행 (depends: Task 5, Task 6)
  - src/capcut_builder.py 실행
  - draft_content.json 생성 → CapCut 프로젝트 폴더
  - 출력: output/capcut_projects/{project_id}/

- [ ] Task 8: QA 검수 (depends: Task 7)
  - 26개 체크리스트 검증
  - 출력: output/qa_report.json

- [ ] Task 9: YouTube 업로드 (depends: Task 8, QA 통과 시)
  - src/youtube_uploader.py 실행
  - 메타데이터 + 영상 업로드
  - 출력: output/youtube_queue/{video_id}.json

---

## 실행 명령

```bash
# 서원토건 채널 첫 영상
python src/orchestrator.py --channel seowon --topic "안전사고 유형 및 대처방법"

# 쥬시톡 채널 첫 영상
python src/orchestrator.py --channel jusi --topic "시니어가 절대 안 알려주는 것들"

# 말하지않는것들 벤치마킹
python src/orchestrator.py --channel unspoken --action benchmark

# Scout만 (기획 단계 검토용)
python src/orchestrator.py --channel seowon --topic "안전사고" --action scout_only
```
