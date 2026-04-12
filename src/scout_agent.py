"""
Scout Agent — 레퍼런스 수집 & 성공 패턴 분석
==============================================
노정호 방법론의 핵심: 전체 시간의 50%를 여기에 투자.
타겟 영상 분석 → 성공 패턴 도출 → concept.md 생성
"""

import json
import os
from pathlib import Path
from typing import List, Dict
import anthropic

# Claude API 클라이언트
client = anthropic.Anthropic()

# ── 채널별 레퍼런스 타겟 ─────────────────────────────────────────────────────
REFERENCE_TARGETS = {
    "seowon": {
        "keywords": ["건설 안전", "현장 안전사고", "산업재해 예방", "안전교육"],
        "channels": ["안전보건공단", "고용노동부", "건설현장 안전"],
        "benchmark_count": 10,
    },
    "jusi": {
        "keywords": ["직장 선배 조언", "시니어 경험", "직장인 꿀팁", "신입 실수"],
        "channels": ["직장인 유튜브", "커리어 조언"],
        "benchmark_count": 10,
    },
    "unspoken": {
        "keywords": ["감성 플레이리스트", "AI 음악", "힐링 음악", "인디 감성"],
        "channels": ["로파이 힙합", "감성 음악 채널"],
        "benchmark_count": 15,  # 음악 채널은 더 많이 벤치마킹
    },
}

# ── 채널별 성공 지표 ─────────────────────────────────────────────────────────
SUCCESS_PATTERNS = {
    "seowon": {
        "hook_patterns": ["실제 사고 사례", "충격적 통계", "당신이 모르는 사실"],
        "title_format": "[경고] {주제} | 현장 전문가가 알려주는 실제 대처법",
        "thumbnail_style": "빨간 경고색 + 실제 현장 이미지 + 충격적 수치",
        "content_structure": ["사고 사례", "원인 분석", "예방법", "대처법", "법적 기준"],
    },
    "jusi": {
        "hook_patterns": ["아무도 안 알려줬던", "10년 해봤더니", "신입때 이걸 알았더라면"],
        "title_format": "{연차}년차가 {주니어}에게 솔직하게 알려주는 {주제}",
        "thumbnail_style": "친근한 얼굴 + 말풍선 + 핵심 문구",
        "content_structure": ["공감 훅", "실수 사례", "배운 점", "실전 팁", "응원 마무리"],
    },
    "unspoken": {
        "hook_patterns": ["새벽에 듣는", "비 오는 날", "혼자 있고 싶을 때"],
        "title_format": "{감성키워드} 플레이리스트 | {상황} 🎵",
        "thumbnail_style": "어두운 무드 + 감성 일러스트 + 영문 타이틀",
        "content_structure": ["인트로 무드", "트랙1~N", "아웃트로"],
    },
}


class ScoutAgent:
    """레퍼런스 수집 & 성공 패턴 분석 에이전트"""

    def __init__(self, channel: str, topic: str, workspace: Path):
        self.channel = channel
        self.topic = topic
        self.workspace = workspace
        self.targets = REFERENCE_TARGETS[channel]
        self.patterns = SUCCESS_PATTERNS[channel]

    def run(self) -> Dict:
        """메인 실행: 레퍼런스 분석 → concept.md 생성"""
        print(f"\n  📡 SCOUT: '{self.topic}' 레퍼런스 분석 시작...")

        # Claude API로 레퍼런스 분석 + 컨셉 생성
        concept = self._generate_concept()

        # concept.md 저장
        concept_path = self.workspace / "concept.md"
        concept_path.write_text(concept, encoding="utf-8")

        print(f"  ✅ concept.md 저장: {concept_path}")
        return {"concept_path": str(concept_path), "content": concept}

    def run_benchmark(self) -> Dict:
        """unspoken 채널 전용: 10만+ 채널 벤치마킹"""
        print(f"\n  📡 BENCHMARK: 10만+ 감성 음악 채널 벤치마킹...")

        benchmark = self._analyze_benchmark_channels()
        bench_path = self.workspace / "benchmark.md"
        bench_path.write_text(benchmark, encoding="utf-8")

        print(f"  ✅ benchmark.md 저장")
        return {"benchmark_path": str(bench_path)}

    def _generate_concept(self) -> str:
        """Claude API로 레퍼런스 기반 컨셉 생성"""

        system_prompt = f"""당신은 유튜브 채널 전략 전문가이자 콘텐츠 기획자입니다.
주어진 채널 특성과 주제를 분석하여 성공 가능성이 높은 영상 컨셉을 도출합니다.

채널: {self.channel}
성공 패턴:
- 훅 패턴: {', '.join(self.patterns['hook_patterns'])}
- 제목 포맷: {self.patterns['title_format']}
- 썸네일: {self.patterns['thumbnail_style']}
- 콘텐츠 구조: {' → '.join(self.patterns['content_structure'])}

반드시 JSON이 아닌 마크다운으로 응답하세요."""

        user_prompt = f"""주제: "{self.topic}"

위 채널의 성공 패턴을 철저히 분석하여 다음을 포함한 concept.md를 작성하세요:

## 1. 레퍼런스 분석 (가상 Top 5)
- 유사 영상 제목, 예상 조회수, 성공 이유 분석

## 2. 타겟 시청자 프로파일
- 누가, 어떤 상황에서, 왜 볼 것인가

## 3. 핵심 훅 (오프닝 15초)
- 시청자를 즉시 사로잡는 오프닝 문장 3개 옵션

## 4. 영상 제목 (SEO 최적화)
- 메인 제목 + 서브타이틀 + 해시태그 5개

## 5. 썸네일 컨셉
- 배경색, 텍스트, 이미지 구성

## 6. 씬 구성 (7~10씬)
- 씬 번호, 내용 요약, 예상 길이(초), 배경 이미지 키워드

## 7. 차별화 포인트
- 경쟁 영상 대비 우리만의 강점"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{"role": "user", "content": user_prompt}],
            system=system_prompt,
        )

        return response.content[0].text

    def _analyze_benchmark_channels(self) -> str:
        """감성 음악 채널 벤치마킹"""

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=3000,
            messages=[{
                "role": "user",
                "content": f"""감성 AI 음악 유튜브 채널 중 조회수 10만+ 달성한 채널들을 벤치마킹하세요.

분석 항목:
1. 성공 채널 Top 5 (가상 분석)
   - 채널명, 추정 구독자, 대표 영상 스타일
2. 공통 성공 패턴
   - 제목 패턴, 썸네일 스타일, 업로드 주기
3. 키워드 전략
   - 검색량 높은 감성 키워드 20개
4. "말하지 않는 것들" 채널 개선 방향
   - 현재 문제점, 개선점, 신규 앨범 컨셉 3개 제안
5. 첫 신규 앨범 추천
   - 제목, 트랙 구성, 예상 반응"""
            }],
        )

        return response.content[0].text
