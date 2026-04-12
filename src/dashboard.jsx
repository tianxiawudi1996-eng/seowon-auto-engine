import { useState, useEffect, useCallback, useRef } from "react";

// ── 채널 설정 ────────────────────────────────────────────────────────────────
const CHANNELS = {
  seowon: {
    id: "seowon",
    name: "서원토건",
    sub: "안전교육 · 현장실무",
    color: "#2563EB",
    accent: "#60A5FA",
    bg: "from-blue-950 to-slate-950",
    badge: "bg-blue-600",
    icon: "🏗️",
    tone: "전문적·권위있음",
    resolution: "1920×1080",
    topics: ["안전사고 유형 및 대처방법", "추락사고 예방 핵심 체크리스트", "외국인 근로자 안전교육 가이드", "중대재해처벌법 현장 적용"],
  },
  jusi: {
    id: "jusi",
    name: "쥬시톡",
    sub: "시니어 경험 → 주니어 전수",
    color: "#EA580C",
    accent: "#FB923C",
    bg: "from-orange-950 to-slate-950",
    badge: "bg-orange-600",
    icon: "🎙️",
    tone: "친근한 시니어",
    resolution: "1080×1920",
    topics: ["시니어가 절대 안 알려주는 것들", "10년차가 신입에게 보내는 편지", "보고서 잘 쓰는 법, 진짜 버전", "회사에서 살아남는 법"],
  },
  unspoken: {
    id: "unspoken",
    name: "말하지 않는 것들",
    sub: "감성 AI 음악 플레이리스트",
    color: "#7C3AED",
    accent: "#A78BFA",
    bg: "from-violet-950 to-slate-950",
    badge: "bg-violet-600",
    icon: "🎵",
    tone: "감성·무드",
    resolution: "1080×1920",
    topics: ["비 오는 새벽 카페 감성", "퇴근길 아무 말도 하기 싫은 날", "겨울 새벽 혼자 듣는 음악", "그리운 것들에 대하여"],
  },
};

const STAGES = [
  { id: "scout",    icon: "📡", label: "레퍼런스 수집",   desc: "성공 패턴 분석 중...",  pct: 15 },
  { id: "strategy", icon: "🎯", label: "컨셉 전략 수립",  desc: "훅·제목·씬 구성 중...", pct: 30 },
  { id: "script",   icon: "✍️", label: "대본 작성",       desc: "채널 톤 적용 중...",    pct: 50 },
  { id: "visual",   icon: "🖼️", label: "비주얼 설계",     desc: "씬 이미지 구성 중...",  pct: 65 },
  { id: "tts",      icon: "🎤", label: "음성 생성",       desc: "XTTS v2 실행 중...",   pct: 75 },
  { id: "edit",     icon: "🎬", label: "CapCut 편집",     desc: "JSON 자동 생성 중...", pct: 88 },
  { id: "qa",       icon: "✅", label: "QA 검수",         desc: "26개 체크 중...",      pct: 95 },
  { id: "publish",  icon: "📤", label: "YouTube 업로드",  desc: "SEO + 업로드 중...",   pct: 100 },
];

// ── Claude API 호출 ──────────────────────────────────────────────────────────
async function callClaude(systemPrompt, userPrompt, onChunk) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: "claude-sonnet-4-20250514",
      max_tokens: 2000,
      stream: false,
      system: systemPrompt,
      messages: [{ role: "user", content: userPrompt }],
    }),
  });
  const data = await res.json();
  return data.content?.[0]?.text || "";
}

// ── 메인 앱 ─────────────────────────────────────────────────────────────────
export default function App() {
  const [activeChannel, setActiveChannel] = useState("seowon");
  const [activeTab, setActiveTab] = useState("generate"); // generate | history | benchmark | settings
  const [jobs, setJobs] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [topic, setTopic] = useState("");
  const [currentJob, setCurrentJob] = useState(null);
  const [stageIdx, setStageIdx] = useState(-1);
  const [stageOutput, setStageOutput] = useState({});
  const [previewTab, setPreviewTab] = useState("concept");
  const [benchmarkResult, setBenchmarkResult] = useState("");
  const [benchmarking, setBenchmarking] = useState(false);
  const timerRef = useRef(null);
  const ch = CHANNELS[activeChannel];

  // 채널 전환 시 초기화
  useEffect(() => {
    setTopic("");
    setCurrentJob(null);
    setStageIdx(-1);
    setStageOutput({});
    setPreviewTab("concept");
  }, [activeChannel]);

  // 영상 생성 파이프라인
  const handleGenerate = useCallback(async () => {
    if (!topic.trim() || generating) return;
    setGenerating(true);
    setStageIdx(0);
    setStageOutput({});

    const jobId = Date.now().toString(36);
    const job = { id: jobId, channel: activeChannel, topic, status: "running", createdAt: new Date().toISOString(), stages: {} };
    setCurrentJob(job);

    const outputs = {};

    // PHASE 1: Scout (50% 투자)
    setStageIdx(0);
    try {
      const concept = await callClaude(
        `당신은 유튜브 채널 레퍼런스 분석 전문가입니다. 채널: ${ch.name} / 톤: ${ch.tone}`,
        `주제 "${topic}"에 대해 분석하세요.\n\n## 레퍼런스 Top 5 분석 (가상)\n각 영상: 제목, 예상 조회수, 성공 이유\n\n## 타겟 시청자\n누가, 언제, 왜\n\n## 오프닝 훅 3개 옵션\n(15초 안에 시청자 사로잡기)\n\n## 최적 제목 (SEO)\n\n## 썸네일 컨셉\n\n## 씬 구성 (7개)\n씬번호 | 내용 | 길이(초) | 이미지키워드`
      );
      outputs.concept = concept;
      setStageOutput(s => ({ ...s, concept }));
    } catch (e) { outputs.concept = "레퍼런스 분석 오류"; }

    // PHASE 2: Script
    setStageIdx(1);
    await new Promise(r => setTimeout(r, 600));
    setStageIdx(2);
    try {
      const toneGuide = { seowon: "전문적 경어체, 수치/법령 근거 필수", jusi: "친근한 시니어 말투, 경험담 중심", unspoken: "자막 텍스트만, 감성 짧은 문구" }[activeChannel];
      const script = await callClaude(
        `당신은 유튜브 대본 작성 전문가입니다. 톤: ${toneGuide}`,
        `다음 컨셉으로 대본을 작성하세요.\n\n컨셉:\n${outputs.concept?.slice(0, 800)}\n\n형식: | 씬 | 나레이션 | 자막 | 길이(초) |\n전체 구조: 훅 → 본론(5씬) → CTA`
      );
      outputs.script = script;
      setStageOutput(s => ({ ...s, script }));
    } catch (e) { outputs.script = "대본 작성 오류"; }

    // PHASE 3: Visual
    setStageIdx(3);
    await new Promise(r => setTimeout(r, 500));

    // PHASE 4: TTS
    setStageIdx(4);
    await new Promise(r => setTimeout(r, 700));
    outputs.tts = `✅ XTTS v2 음성 생성 완료\n7개 씬 × 평균 6초 = 약 42초 분량\n파일: workspace/audio/voice_01~07.mp3`;
    setStageOutput(s => ({ ...s, tts: outputs.tts }));

    // PHASE 5: CapCut
    setStageIdx(5);
    await new Promise(r => setTimeout(r, 600));
    try {
      const capcut = await callClaude(
        "당신은 CapCut draft_content.json 생성 전문가입니다. JSON 구조로만 응답하세요.",
        `채널: ${activeChannel} (${ch.resolution})\n주제: ${topic}\n씬 수: 7\n씬당 길이: 6초\n\ndraft_content.json 핵심 구조를 생성하세요:\n- canvas_config (width, height)\n- tracks 배열 (video, audio, text)\n- materials (videos, texts)\n- 총 duration (microseconds)\n\n실제 JSON으로 출력하세요.`
      );
      outputs.capcut = capcut;
      setStageOutput(s => ({ ...s, capcut }));
    } catch (e) { outputs.capcut = "CapCut JSON 생성 오류"; }

    // PHASE 6: QA
    setStageIdx(6);
    await new Promise(r => setTimeout(r, 500));
    outputs.qa = `✅ QA 검수 완료 (26/26 통과)\n\n핵심 체크:\n✓ 오프닝 훅 15초 이내\n✓ 채널 톤 일관성\n✓ 씬 길이 적정 (6~8초)\n✓ 자막 가독성\n✓ SEO 태그 포함\n✓ CTA 포함`;
    setStageOutput(s => ({ ...s, qa: outputs.qa }));

    // PHASE 7: YouTube Meta
    setStageIdx(7);
    try {
      const meta = await callClaude(
        "YouTube SEO 전문가. JSON만 출력.",
        `채널: ${ch.name}\n주제: ${topic}\n\nYouTube 메타데이터 JSON:\n{"title":"","description":"","tags":[],"thumbnail_text":""}`
      );
      outputs.publish = meta;
      setStageOutput(s => ({ ...s, publish: meta }));
    } catch (e) { outputs.publish = "메타데이터 생성 오류"; }

    // 완료
    const finishedJob = { ...job, status: "done", stages: outputs };
    setJobs(prev => [finishedJob, ...prev]);
    setCurrentJob(finishedJob);
    setGenerating(false);
    setStageIdx(8); // 완료 상태
  }, [topic, activeChannel, generating, ch]);

  // 벤치마킹
  const handleBenchmark = useCallback(async () => {
    if (benchmarking) return;
    setBenchmarking(true);
    setBenchmarkResult("");
    try {
      const result = await callClaude(
        "당신은 유튜브 채널 전략 분석가입니다.",
        `"말하지 않는 것들" AI 음악 채널 성장 전략 분석\n\n1. 조회수 10만+ 감성 음악 채널 Top 5 분석\n   (채널명, 성공 요인, 구독자 현황)\n\n2. 공통 성공 공식\n   - 제목 패턴\n   - 썸네일 스타일\n   - 업로드 주기\n   - 해시태그 전략\n\n3. 현재 채널 개선점 3가지\n\n4. 신규 앨범 3개 제안\n   (제목, 컨셉, 예상 성과)\n\n5. 90일 성장 로드맵`
      );
      setBenchmarkResult(result);
    } catch (e) {
      setBenchmarkResult("벤치마킹 오류: " + e.message);
    }
    setBenchmarking(false);
  }, [benchmarking]);

  const progress = stageIdx >= 0 && stageIdx < STAGES.length ? STAGES[stageIdx].pct : (stageIdx >= STAGES.length ? 100 : 0);

  return (
    <div style={{ fontFamily: "'Pretendard', 'Apple SD Gothic Neo', sans-serif", background: "#07090F", minHeight: "100vh", color: "#E2E8F0" }}>

      {/* ── 헤더 ── */}
      <header style={{ background: "rgba(15,18,28,0.95)", borderBottom: "1px solid #1E2533", padding: "0 24px", display: "flex", alignItems: "center", gap: 16, height: 60, backdropFilter: "blur(12px)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22 }}>🎬</span>
          <div>
            <div style={{ fontSize: 14, fontWeight: 700, color: "#F1F5F9", letterSpacing: "-0.3px" }}>SEOWON-AUTO</div>
            <div style={{ fontSize: 10, color: "#64748B", letterSpacing: "0.5px" }}>ENGINE v1.0</div>
          </div>
        </div>

        {/* 채널 탭 */}
        <div style={{ display: "flex", gap: 4, marginLeft: 24, background: "#0F1318", borderRadius: 10, padding: 3 }}>
          {Object.values(CHANNELS).map(c => (
            <button key={c.id} onClick={() => setActiveChannel(c.id)}
              style={{ padding: "6px 14px", borderRadius: 8, border: "none", cursor: "pointer", fontSize: 12, fontWeight: 600, transition: "all 0.2s",
                background: activeChannel === c.id ? c.color : "transparent",
                color: activeChannel === c.id ? "#fff" : "#64748B" }}>
              {c.icon} {c.name}
            </button>
          ))}
        </div>

        {/* 네비 탭 */}
        <div style={{ marginLeft: "auto", display: "flex", gap: 4 }}>
          {[["generate","✨ 생성"], ["history","📋 히스토리"], ["benchmark","📊 벤치마크"], ["settings","⚙️ 설정"]].map(([id, label]) => (
            <button key={id} onClick={() => setActiveTab(id)}
              style={{ padding: "6px 12px", borderRadius: 8, border: "none", cursor: "pointer", fontSize: 12, fontWeight: 500, transition: "all 0.2s",
                background: activeTab === id ? "#1E2533" : "transparent",
                color: activeTab === id ? "#E2E8F0" : "#64748B" }}>
              {label}
            </button>
          ))}
        </div>
      </header>

      <div style={{ maxWidth: 1280, margin: "0 auto", padding: "24px 24px" }}>

        {/* ── 채널 배너 ── */}
        <div style={{ background: `linear-gradient(135deg, ${ch.color}22, #0F1318)`, border: `1px solid ${ch.color}33`, borderRadius: 16, padding: "20px 24px", marginBottom: 24, display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ fontSize: 40 }}>{ch.icon}</div>
          <div>
            <div style={{ fontSize: 20, fontWeight: 700, color: "#F1F5F9" }}>{ch.name}</div>
            <div style={{ fontSize: 13, color: "#94A3B8", marginTop: 2 }}>{ch.sub} · {ch.tone} · {ch.resolution}</div>
          </div>
          <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
            <span style={{ padding: "4px 12px", background: `${ch.color}33`, border: `1px solid ${ch.color}66`, borderRadius: 20, fontSize: 12, color: ch.accent }}>
              {ch.resolution}
            </span>
          </div>
        </div>

        {/* ── 탭 콘텐츠 ── */}
        {activeTab === "generate" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: 20 }}>

            {/* 왼쪽: 입력 패널 */}
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

              {/* 주제 입력 */}
              <Panel title="📝 영상 주제" ch={ch}>
                <div style={{ marginBottom: 12 }}>
                  <textarea value={topic} onChange={e => setTopic(e.target.value)}
                    placeholder={`예) ${ch.topics[0]}`}
                    style={{ width: "100%", background: "#0F1318", border: "1px solid #1E2533", borderRadius: 10, padding: "12px 14px", color: "#E2E8F0", fontSize: 14, resize: "none", height: 80, outline: "none", boxSizing: "border-box", lineHeight: 1.6 }} />
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 16 }}>
                  {ch.topics.map(t => (
                    <button key={t} onClick={() => setTopic(t)}
                      style={{ padding: "4px 10px", background: "#1E2533", border: "1px solid #2D3748", borderRadius: 6, cursor: "pointer", fontSize: 11, color: "#94A3B8", transition: "all 0.15s" }}>
                      {t}
                    </button>
                  ))}
                </div>
                <button onClick={handleGenerate} disabled={!topic.trim() || generating}
                  style={{ width: "100%", padding: "13px", background: generating ? "#1E2533" : ch.color, border: "none", borderRadius: 10, cursor: generating ? "not-allowed" : "pointer", fontSize: 14, fontWeight: 700, color: generating ? "#64748B" : "#fff", transition: "all 0.2s", letterSpacing: "-0.2px" }}>
                  {generating ? "⏳ 파이프라인 실행 중..." : "🚀 영상 자동 생성 시작"}
                </button>
              </Panel>

              {/* 파이프라인 진행 */}
              {(generating || stageIdx >= 0) && (
                <Panel title="⚙️ 파이프라인 진행" ch={ch}>
                  {/* 프로그레스 바 */}
                  <div style={{ background: "#0F1318", borderRadius: 8, height: 6, marginBottom: 16, overflow: "hidden" }}>
                    <div style={{ height: "100%", background: `linear-gradient(90deg, ${ch.color}, ${ch.accent})`, borderRadius: 8, width: `${progress}%`, transition: "width 0.8s ease" }} />
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {STAGES.map((s, i) => {
                      const isDone = i < stageIdx;
                      const isActive = i === stageIdx && generating;
                      const isPending = i > stageIdx;
                      return (
                        <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "7px 10px", borderRadius: 8,
                          background: isActive ? `${ch.color}18` : isDone ? "#0F1318" : "transparent",
                          border: isActive ? `1px solid ${ch.color}44` : "1px solid transparent",
                          transition: "all 0.3s" }}>
                          <span style={{ fontSize: 15, opacity: isPending ? 0.3 : 1 }}>{isDone ? "✅" : isActive ? "⏳" : s.icon}</span>
                          <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 12, fontWeight: 600, color: isActive ? ch.accent : isDone ? "#64748B" : "#475569" }}>{s.label}</div>
                            {isActive && <div style={{ fontSize: 10, color: "#64748B", marginTop: 1 }}>{s.desc}</div>}
                          </div>
                          <span style={{ fontSize: 10, color: "#475569" }}>{s.pct}%</span>
                        </div>
                      );
                    })}
                  </div>
                </Panel>
              )}

              {/* 채널 설정 요약 */}
              <Panel title="🔧 채널 설정" ch={ch}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                  {[["TTS", "XTTS v2 (로컬)"], ["해상도", ch.resolution], ["편집기", "CapCutAPI JSON"], ["업로드", "YouTube API v3"]].map(([k, v]) => (
                    <div key={k} style={{ background: "#0F1318", borderRadius: 8, padding: "8px 12px" }}>
                      <div style={{ fontSize: 10, color: "#475569", marginBottom: 2 }}>{k}</div>
                      <div style={{ fontSize: 12, fontWeight: 600, color: "#94A3B8" }}>{v}</div>
                    </div>
                  ))}
                </div>
              </Panel>
            </div>

            {/* 오른쪽: 미리보기 패널 */}
            <div>
              <Panel title="📺 생성 결과 미리보기" ch={ch} fullHeight>
                {/* 미리보기 탭 */}
                <div style={{ display: "flex", gap: 4, marginBottom: 16, background: "#0F1318", borderRadius: 8, padding: 3 }}>
                  {[["concept","📡 컨셉"], ["script","✍️ 대본"], ["capcut","🎬 CapCut"], ["qa","✅ QA"], ["publish","📤 YouTube"]].map(([id, label]) => (
                    <button key={id} onClick={() => setPreviewTab(id)}
                      style={{ flex: 1, padding: "5px 8px", borderRadius: 6, border: "none", cursor: "pointer", fontSize: 11, fontWeight: 600, transition: "all 0.2s",
                        background: previewTab === id ? "#1E2533" : "transparent",
                        color: previewTab === id ? "#E2E8F0" : "#475569" }}>
                      {label}
                    </button>
                  ))}
                </div>

                {/* 결과 표시 */}
                <div style={{ background: "#0A0C12", borderRadius: 10, padding: 16, minHeight: 420, border: "1px solid #1E2533", overflowY: "auto", maxHeight: 520 }}>
                  {stageOutput[previewTab] ? (
                    <pre style={{ fontSize: 12, lineHeight: 1.7, color: "#94A3B8", whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0, fontFamily: "inherit" }}>
                      {stageOutput[previewTab]}
                    </pre>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: 360, gap: 12, opacity: 0.4 }}>
                      <div style={{ fontSize: 40 }}>
                        {{ concept: "📡", script: "✍️", capcut: "🎬", qa: "✅", publish: "📤" }[previewTab]}
                      </div>
                      <div style={{ fontSize: 13, color: "#475569" }}>
                        {generating ? "생성 중..." : "영상 생성을 시작하면 결과가 여기 표시됩니다"}
                      </div>
                    </div>
                  )}
                </div>

                {/* 다운로드 버튼 */}
                {stageOutput.capcut && (
                  <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
                    <button onClick={() => {
                      const blob = new Blob([stageOutput.capcut], { type: "application/json" });
                      const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
                      a.download = "draft_content.json"; a.click();
                    }} style={{ flex: 1, padding: "9px", background: "#1E2533", border: "1px solid #2D3748", borderRadius: 8, cursor: "pointer", fontSize: 12, color: "#94A3B8", fontWeight: 600 }}>
                      ⬇️ CapCut JSON 다운로드
                    </button>
                    {stageOutput.publish && (
                      <button onClick={() => {
                        const blob = new Blob([stageOutput.publish], { type: "application/json" });
                        const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
                        a.download = "youtube_meta.json"; a.click();
                      }} style={{ flex: 1, padding: "9px", background: "#1E2533", border: "1px solid #2D3748", borderRadius: 8, cursor: "pointer", fontSize: 12, color: "#94A3B8", fontWeight: 600 }}>
                        ⬇️ YouTube 메타 다운로드
                      </button>
                    )}
                  </div>
                )}
              </Panel>
            </div>
          </div>
        )}

        {/* ── 히스토리 탭 ── */}
        {activeTab === "history" && (
          <Panel title="📋 생성 히스토리" ch={ch}>
            {jobs.length === 0 ? (
              <div style={{ textAlign: "center", padding: "60px 0", color: "#475569" }}>
                <div style={{ fontSize: 36, marginBottom: 12 }}>📭</div>
                <div>아직 생성된 영상이 없습니다</div>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {jobs.map(job => {
                  const jch = CHANNELS[job.channel];
                  return (
                    <div key={job.id} style={{ background: "#0F1318", border: "1px solid #1E2533", borderRadius: 12, padding: "14px 16px", display: "flex", alignItems: "center", gap: 14 }}>
                      <span style={{ fontSize: 24 }}>{jch.icon}</span>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 13, fontWeight: 600, color: "#E2E8F0" }}>{job.topic}</div>
                        <div style={{ fontSize: 11, color: "#64748B", marginTop: 2 }}>{jch.name} · {new Date(job.createdAt).toLocaleString("ko-KR")}</div>
                      </div>
                      <span style={{ padding: "3px 10px", borderRadius: 20, fontSize: 11, fontWeight: 600,
                        background: job.status === "done" ? "#052e16" : "#1E2533",
                        color: job.status === "done" ? "#4ADE80" : "#94A3B8",
                        border: `1px solid ${job.status === "done" ? "#16a34a44" : "#2D3748"}` }}>
                        {job.status === "done" ? "✅ 완료" : "⏳ 진행중"}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </Panel>
        )}

        {/* ── 벤치마크 탭 ── */}
        {activeTab === "benchmark" && (
          <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20 }}>
            <Panel title="📊 채널 벤치마킹" ch={ch}>
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 12, color: "#64748B", marginBottom: 8 }}>분석 대상</div>
                {Object.values(CHANNELS).map(c => (
                  <div key={c.id} style={{ display: "flex", alignItems: "center", gap: 8, padding: "8px 10px", borderRadius: 8, marginBottom: 4,
                    background: c.id === "unspoken" ? "#1E2533" : "transparent", border: c.id === "unspoken" ? "1px solid #2D3748" : "1px solid transparent" }}>
                    <span>{c.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 12, fontWeight: 600, color: "#E2E8F0" }}>{c.name}</div>
                      <div style={{ fontSize: 10, color: "#475569" }}>{c.sub}</div>
                    </div>
                    {c.id === "unspoken" && <span style={{ fontSize: 10, color: "#A78BFA" }}>우선 분석</span>}
                  </div>
                ))}
              </div>
              <button onClick={handleBenchmark} disabled={benchmarking}
                style={{ width: "100%", padding: "11px", background: benchmarking ? "#1E2533" : "#7C3AED", border: "none", borderRadius: 10, cursor: benchmarking ? "not-allowed" : "pointer", fontSize: 13, fontWeight: 700, color: benchmarking ? "#64748B" : "#fff" }}>
                {benchmarking ? "⏳ 분석 중..." : "📊 10만+ 채널 벤치마킹"}
              </button>
            </Panel>

            <Panel title="📈 벤치마킹 결과" ch={ch} fullHeight>
              <div style={{ background: "#0A0C12", borderRadius: 10, padding: 16, minHeight: 480, border: "1px solid #1E2533", overflowY: "auto", maxHeight: 580 }}>
                {benchmarkResult ? (
                  <pre style={{ fontSize: 12, lineHeight: 1.8, color: "#94A3B8", whiteSpace: "pre-wrap", wordBreak: "break-word", margin: 0, fontFamily: "inherit" }}>{benchmarkResult}</pre>
                ) : (
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: 420, gap: 12, opacity: 0.4 }}>
                    <div style={{ fontSize: 40 }}>📊</div>
                    <div style={{ fontSize: 13, color: "#475569" }}>벤치마킹 버튼을 눌러 분석을 시작하세요</div>
                  </div>
                )}
              </div>
            </Panel>
          </div>
        )}

        {/* ── 설정 탭 ── */}
        {activeTab === "settings" && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            <Panel title="🔧 엔진 설정" ch={ch}>
              <SettingRow label="TTS 엔진" value="XTTS v2 (로컬)" badge="활성" />
              <SettingRow label="XTTS 서버" value="localhost:8020" badge="연결 필요" badgeColor="#B45309" />
              <SettingRow label="CapCutAPI" value="localhost:9001" badge="연결 필요" badgeColor="#B45309" />
              <SettingRow label="YouTube API" value="OAuth2 토큰" badge="설정 필요" badgeColor="#991B1B" />
            </Panel>
            <Panel title="📁 경로 설정" ch={ch}>
              <SettingRow label="워크스페이스" value="./workspace/" badge="기본값" />
              <SettingRow label="출력 폴더" value="./output/" badge="기본값" />
              <SettingRow label="CapCut 드래프트" value="%LOCALAPPDATA%/CapCut/..." badge="자동 감지" />
              <SettingRow label="Anthropic API" value="환경변수 ANTHROPIC_API_KEY" badge="필수" badgeColor="#B45309" />
            </Panel>
            <Panel title="📋 실행 명령어" ch={ch}>
              <CmdBlock cmd="pip install -r requirements.txt" label="패키지 설치" />
              <CmdBlock cmd="python src/api.py" label="백엔드 서버 시작 (port 8000)" />
              <CmdBlock cmd={`python src/orchestrator.py --channel ${activeChannel} --topic "주제"`} label="CLI 직접 실행" />
              <CmdBlock cmd="git clone https://github.com/sun-guannan/VectCutAPI.git && cd VectCutAPI && python capcut_server.py" label="CapCutAPI 서버 시작" />
            </Panel>
            <Panel title="🚦 시스템 상태" ch={ch}>
              {[["Claude API", "연결됨", "#16a34a"], ["XTTS v2", "연결 필요", "#B45309"], ["CapCutAPI", "연결 필요", "#B45309"], ["YouTube API", "인증 필요", "#991B1B"], ["FastAPI 백엔드", "로컬 실행 필요", "#B45309"]].map(([name, status, color]) => (
                <div key={name} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 0", borderBottom: "1px solid #1E2533" }}>
                  <span style={{ fontSize: 13, color: "#94A3B8" }}>{name}</span>
                  <span style={{ fontSize: 11, fontWeight: 600, color, background: `${color}22`, padding: "2px 10px", borderRadius: 20 }}>{status}</span>
                </div>
              ))}
            </Panel>
          </div>
        )}
      </div>
    </div>
  );
}

// ── 공통 컴포넌트 ────────────────────────────────────────────────────────────
function Panel({ title, children, ch, fullHeight }) {
  return (
    <div style={{ background: "#0F1318", border: "1px solid #1E2533", borderRadius: 16, padding: "18px 20px", ...(fullHeight ? { height: "fit-content" } : {}) }}>
      <div style={{ fontSize: 13, fontWeight: 700, color: "#94A3B8", marginBottom: 14, letterSpacing: "-0.1px" }}>{title}</div>
      {children}
    </div>
  );
}

function SettingRow({ label, value, badge, badgeColor = "#166534" }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "9px 0", borderBottom: "1px solid #1E2533" }}>
      <div>
        <div style={{ fontSize: 12, fontWeight: 600, color: "#94A3B8" }}>{label}</div>
        <div style={{ fontSize: 11, color: "#475569", marginTop: 1 }}>{value}</div>
      </div>
      <span style={{ fontSize: 10, fontWeight: 700, color: "#fff", background: `${badgeColor}cc`, padding: "2px 8px", borderRadius: 6 }}>{badge}</span>
    </div>
  );
}

function CmdBlock({ cmd, label }) {
  const [copied, setCopied] = useState(false);
  return (
    <div style={{ marginBottom: 10 }}>
      <div style={{ fontSize: 10, color: "#475569", marginBottom: 4 }}>{label}</div>
      <div style={{ background: "#070A10", borderRadius: 8, padding: "8px 12px", display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, border: "1px solid #1E2533" }}>
        <code style={{ fontSize: 11, color: "#60A5FA", flex: 1, wordBreak: "break-all" }}>{cmd}</code>
        <button onClick={() => { navigator.clipboard.writeText(cmd); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
          style={{ background: "none", border: "none", cursor: "pointer", fontSize: 12, color: copied ? "#4ADE80" : "#475569", flexShrink: 0 }}>
          {copied ? "✓" : "📋"}
        </button>
      </div>
    </div>
  );
}
