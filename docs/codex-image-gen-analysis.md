# 🖼️ ChatGPT(Codex) 구독자 이미지 생성 분석

> 작성: 2026.04.21 | 참조: https://youtu.be/mvQnS_aQJf8

---

## 핵심 정리

ChatGPT 구독자는 GPT-Image(구 DALL-E 후속)로 이미지 생성 가능.
완전 무제한은 아니고 요금제별로 다름.

## 요금제별 이미지 생성 한도

| 요금제 | 월 비용 | 이미지 생성 | 비고 |
|--------|---------|-----------|------|
| 무료 | $0 | 제한 많음 | |
| Plus | $20 | 여유있는 한도 | 짧은 시간 대량 생성 시 제한 |
| Pro $100 | $100 | Plus의 5배 | 신설 요금제 |
| Pro $200 | $200 | **한도 무제한** | ChatGPT Pro 가입자 한정 기능 |

## GPT-Image 모델 특징

- 2025년 3월 26일 출시 (GPT-4o 기반)
- 기존 DALL-E 완전 대체
- Autoregressive 방식 (Diffusion 아님)
- 한글 텍스트 포함 이미지 생성 가능
- API명: gpt-image-1

## ⚠️ 파이프라인 적용 시 핵심 구분

### ChatGPT 웹 UI (chatgpt.com)
- 구독료만으로 이미지 생성 가능
- 하지만 자동화 파이프라인 연결 어려움 (수동 사용만)

### API (gpt-image-1)
- 자동화 파이프라인에 연결 가능
- 구독과 별개로 이미지당 별도 과금
- 1024x1024 기준 약 $0.04/장

## SEOWON-AUTO ENGINE 적용 전략

### 현재 (Gemini API 사용)
- Gemini 2.0 Flash: 텍스트 생성 무료 월 1,500회
- 이미지: Imagen 3 API 별도 (유료)

### 추천 방법 (비용 0원)
1. Stable Diffusion 로컬 실행 → 완전 무료
   - Galaxy Book5 Ultra Intel Arc 140V 지원 확인 필요
2. Gemini Imagen 3 API → 월 무료 한도 있음
3. ChatGPT Playwright 자동화 → 구독 이미지 활용 (회색지대)

### 결론
씬별 이미지는 당장 Stable Diffusion 로컬로 해결하는 게 최적.
비용 0원 + 완전 자동화 + 품질 우수.

