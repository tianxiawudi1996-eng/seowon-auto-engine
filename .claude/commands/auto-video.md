# /auto-video

유튜브 영상 완전 자동 생성 파이프라인을 실행합니다.

## 사용법

```
/auto-video --channel [seowon|jusi|unspoken] --topic "주제"
/auto-video --channel unspoken --action benchmark
```

## 실행 순서

1. CLAUDE.md 로드 및 채널 설정 확인
2. prompt_plan.md에서 태스크 DAG 파싱
3. Wave 1: Scout + Strategist 병렬 실행
4. Wave 2: Script + Visual 병렬 실행
5. Wave 3: TTS + Subtitle 병렬 실행
6. Wave 4: Editor → QA → Publisher 순차 실행
7. 완료 리포트 출력

## 에이전트 팀 구성

Agent Teams 실험 기능 활성화 필요:
```json
{"env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}}
```

팀 구성:
- Implementer 1: Scout + Script 담당
- Implementer 2: Visual + TTS 담당  
- Verifier: QA + Publisher 담당

## 실행

```bash
python src/orchestrator.py --channel $CHANNEL --topic "$TOPIC"
```
