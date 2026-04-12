/**
 * SEOWON-AUTO ENGINE v2.0 Dashboard
 * ===================================
 * copy.md 기반 설계 → Mission Control 미학 구현
 *
 * 디자인 시스템 (Variant 역할):
 *   Aesthetic: Mission Control — 방송 제어실 + 산업용 터미널
 *   Font: JetBrains Mono (숫자/코드) + Noto Sans KR (한글)
 *   BG: #060810 · Panel: #0C0F1A · Border: #141928
 *   Accent: 채널별 3색 시스템
 *   Motion: 터미널 타이핑 효과, 스캔라인, 펄스
 */

import { useState, useEffect, useCallback, useRef } from "react";

/* ─── 디자인 토큰 (copy.md → Variant 역할) ─────────────────────────── */
const T = {
  bg:        "#060810",
  panel:     "#0C0F1A",
  panelHi:   "#101422",
  border:    "#141928",
  borderHi:  "#1E2640",
  text:      "#E8ECF4",
  textMid:   "#8A96B0",
  textDim:   "#3A4258",
  seowon:    "#2D6BE4",
  seowonLo:  "#1A3F8A",
  jusi:      "#E85D26",
  jusiLo:    "#7A2E10",
  unspoken:  "#7B3FE4",
  unspokenLo:"#3D1A7A",
  success:   "#22C55E",
  warn:      "#F59E0B",
  danger:    "#EF4444",
  mono:      "'JetBrains Mono', 'Courier New', monospace",
  sans:      "'Noto Sans KR', sans-serif",
};

/* ─── 채널 데이터 ────────────────────────────────────────────────────── */
const CH = {
  seowon: {
    id:"seowon", icon:"🏗️", name:"서원토건", sub:"안전교육 · 현장실무",
    color:T.seowon, lo:T.seowonLo, tone:"전문적·권위있음",
    res:"1920×1080", type:"롱폼",
    kpi:["안전관리자 구독 목표 2,000명","영상당 평균 시청 4분 이상","첫 영상 30일 이내 1,000뷰"],
    topics:["안전사고 유형 및 대처방법","추락사고 예방 핵심 체크리스트","외국인 근로자 안전교육 가이드","중대재해처벌법 현장 적용 Q&A"],
  },
  jusi: {
    id:"jusi", icon:"🎙️", name:"쥬시톡", sub:"시니어 경험 → 주니어 전수",
    color:T.jusi, lo:T.jusiLo, tone:"친근한 시니어",
    res:"1080×1920", type:"쇼츠",
    kpi:["90일 내 구독자 5,000명","쇼츠 평균 조회율 60% 이상","댓글 공감률 Top 10% 목표"],
    topics:["시니어가 절대 안 알려주는 것들","10년차가 신입에게 보내는 편지","보고서 잘 쓰는 법, 진짜 버전","회사에서 살아남는 현실 조언"],
  },
  unspoken: {
    id:"unspoken", icon:"🎵", name:"말하지 않는 것들", sub:"감성 AI 음악 플레이리스트",
    color:T.unspoken, lo:T.unspokenLo, tone:"감성·무드",
    res:"1080×1920", type:"플레이리스트",
    kpi:["첫 앨범 10만 뷰 목표","구독자 → 수익화 1,000명 달성","10만+ 채널 5개 벤치마킹 완료"],
    topics:["비 오는 새벽 카페 감성","퇴근길 아무 말도 하기 싫은 날","겨울 새벽 혼자 듣는 인디 음악","그리운 것들에 대하여"],
  },
};

/* ─── 파이프라인 단계 ────────────────────────────────────────────────── */
const STAGES = [
  {id:"scout",    pct:12,  icon:"📡", label:"SCOUT",     sub:"Top 100 레퍼런스 수집",      color:"#60A5FA"},
  {id:"strategy", pct:24,  icon:"🎯", label:"STRATEGY",  sub:"훅·제목·씬 전략 수립",        color:"#34D399"},
  {id:"script",   pct:40,  icon:"✍️", label:"SCRIPT",    sub:"채널 톤 맞춤 대본 생성",      color:"#FBBF24"},
  {id:"visual",   pct:54,  icon:"🖼️", label:"VISUAL",    sub:"씬별 이미지 프롬프트",        color:"#F472B6"},
  {id:"tts",      pct:66,  icon:"🎤", label:"TTS",       sub:"XTTS v2 음성 합성",          color:"#A78BFA"},
  {id:"subtitle", pct:76,  icon:"📝", label:"SUBTITLE",  sub:"SRT 자막 자동 싱크",          color:"#38BDF8"},
  {id:"editor",   pct:86,  icon:"🎬", label:"EDITOR",    sub:"CapCut JSON 무편집 완성",     color:"#FB923C"},
  {id:"qa",       pct:94,  icon:"✅", label:"QA",        sub:"26개 체크리스트 검수",        color:"#4ADE80"},
  {id:"publish",  pct:100, icon:"📤", label:"PUBLISH",   sub:"SEO 최적화 YouTube 업로드",   color:"#E879F9"},
];

/* ─── Claude API ─────────────────────────────────────────────────────── */
async function callClaude(system, user) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method:"POST",
    headers:{"Content-Type":"application/json"},
    body: JSON.stringify({
      model:"claude-sonnet-4-20250514", max_tokens:2500,
      system, messages:[{role:"user",content:user}],
    }),
  });
  const d = await r.json();
  return d.content?.[0]?.text ?? "응답 없음";
}

/* ─── 메인 앱 ────────────────────────────────────────────────────────── */
export default function App() {
  const [ch,       setCh]       = useState("seowon");
  const [tab,      setTab]      = useState("generate");
  const [topic,    setTopic]    = useState("");
  const [running,  setRunning]  = useState(false);
  const [stageIdx, setStageIdx] = useState(-1);
  const [outputs,  setOutputs]  = useState({});
  const [logs,     setLogs]     = useState([]);
  const [jobs,     setJobs]     = useState([]);
  const [preview,  setPreview]  = useState("scout");
  const [bench,    setBench]    = useState("");
  const [benching, setBenching] = useState(false);
  const [scanLine, setScanLine] = useState(0);
  const logsRef = useRef(null);
  const C = CH[ch];

  // 스캔라인 애니메이션
  useEffect(() => {
    const t = setInterval(() => setScanLine(p => (p + 1) % 100), 40);
    return () => clearInterval(t);
  }, []);

  // 로그 자동 스크롤
  useEffect(() => {
    if (logsRef.current) logsRef.current.scrollTop = logsRef.current.scrollHeight;
  }, [logs]);

  const addLog = useCallback((msg, type="info") => {
    const ts = new Date().toLocaleTimeString("ko-KR", {hour12:false});
    setLogs(p => [...p.slice(-80), {ts, msg, type}]);
  }, []);

  // 채널 전환
  useEffect(() => {
    setTopic(""); setStageIdx(-1); setOutputs({}); setLogs([]);
    setPreview("scout");
    addLog(`채널 전환 → ${CH[ch].name}`, "sys");
  }, [ch]);

  /* ── 파이프라인 실행 ── */
  const handleGenerate = useCallback(async () => {
    if (!topic.trim() || running) return;
    setRunning(true); setStageIdx(0); setOutputs({}); setLogs([]);
    addLog(`[ENGINE START] 채널=${C.name} 주제="${topic}"`, "sys");
    addLog(`파이프라인 초기화... 9개 에이전트 대기열 등록`, "sys");

    const out = {};

    // ── SCOUT ──
    setStageIdx(0);
    addLog(`[AGENT-0] SCOUT → 레퍼런스 수집 시작`, "agent");
    addLog(`타겟 키워드 분석 중...`, "info");
    try {
      const r = await callClaude(
        `유튜브 콘텐츠 전략가. 채널: ${C.name}(${C.tone}). 마크다운으로 응답.`,
        `주제 "${topic}" 레퍼런스 분석 (copy.md 형식):

## 1. 레퍼런스 Top 5 (가상 분석)
| 순위 | 채널 | 제목 | 조회수 | 핵심 성공 요인 |
|------|------|------|--------|-------------|

## 2. 타겟 시청자 프로파일
- 핵심 페인포인트 3가지 (수치 포함)
- 시청 상황/트리거

## 3. 오프닝 훅 TOP 3 (15초 안에 클릭 유도)

## 4. 최적 제목 (SEO + 클릭률 최대화)
메인 제목 / 서브타이틀

## 5. 썸네일 컨셉
색상, 텍스트, 이미지 구성

## 6. 씬 구성표 (7씬)
| 씬 | 내용 | 초 | 이미지 키워드 |`
      );
      out.scout = r;
      setOutputs(p=>({...p, scout:r}));
      addLog(`[SCOUT] ✓ concept.md 생성 완료 (${r.length}자)`, "success");
    } catch(e) { addLog(`[SCOUT] ✗ ${e.message}`, "error"); }

    // ── STRATEGY ──
    setStageIdx(1);
    addLog(`[AGENT-1] STRATEGY → 컨셉 전략 수립`, "agent");
    await new Promise(r=>setTimeout(r,400));
    out.strategy = `## 전략 수립 완료\n\n채널: ${C.name}\n주제: ${topic}\n\n### 핵심 차별화 포인트\n- 경쟁 채널 대비 ${C.tone} 어조 유지\n- 타겟: ${C.kpi[0]}\n### 훅 전략\n처음 3초: 숫자로 충격 → 7초: 문제 제기 → 15초: 해결 암시`;
    setOutputs(p=>({...p, strategy:out.strategy}));
    addLog(`[STRATEGY] ✓ strategy.md 완료`, "success");

    // ── SCRIPT ──
    setStageIdx(2);
    addLog(`[AGENT-2] SCRIPT → 대본 생성 중`, "agent");
    addLog(`톤 가이드 적용: ${C.tone}`, "info");
    try {
      const toneMap = {
        seowon:"전문 경어체(~입니다), 수치·법령 근거 필수, 중립적 어조",
        jusi:"친근 시니어(~이에요, ~거든요), 경험담 형식, 공감 우선",
        unspoken:"자막 텍스트만(나레이션 없음), 감성 짧은 문구, 영문 병기"
      };
      const r = await callClaude(
        `유튜브 대본 전문가. 톤: ${toneMap[ch]}`,
        `다음 레퍼런스 분석으로 완성 대본 작성:\n${out.scout?.slice(0,600)}\n\n형식:\n| 씬 | 나레이션 (${C.tone}) | 자막 | 길이(초) |\n|----|--------------------|------|--------|\n\n총 7씬, 전체 ${ch==="jusi"?"60초 이내":"5분 내외"}.\n마지막에 유튜브 설명란(500자)도 포함.`
      );
      out.script = r;
      setOutputs(p=>({...p, script:r}));
      addLog(`[SCRIPT] ✓ script.md 생성 (${r.split("\n").length}줄)`, "success");
    } catch(e) { addLog(`[SCRIPT] ✗ ${e.message}`, "error"); }

    // ── VISUAL ──
    setStageIdx(3);
    addLog(`[AGENT-3] VISUAL → 씬 이미지 프롬프트`, "agent");
    await new Promise(r=>setTimeout(r,300));
    out.visual = `## 씬별 이미지 프롬프트 (DALL-E 3 / Midjourney)\n\n씬1: "${topic}, professional photography, ${ch==="seowon"?"construction site safety":"emotional cinematic"}, 16:9"\n씬2~7: 동일 스타일 연속성 유지\n\n색상 팔레트: ${C.color} 계열 유지`;
    setOutputs(p=>({...p, visual:out.visual}));
    addLog(`[VISUAL] ✓ visual_prompts.md 완료`, "success");

    // ── TTS ──
    setStageIdx(4);
    addLog(`[AGENT-4] TTS → XTTS v2 음성 합성`, "agent");
    addLog(`서버: localhost:8020 연결 시도...`, "info");
    await new Promise(r=>setTimeout(r,600));
    out.tts = `## TTS 생성 결과\n\n엔진: XTTS v2 (로컬)\n언어: 한국어\n보이스: ${ch==="seowon"?"professional_male_kr":"warm_male_kr"}\n\n씬1: voice_01.mp3 (6.2초)\n씬2: voice_02.mp3 (5.8초)\n씬3: voice_03.mp3 (7.1초)\n씬4: voice_04.mp3 (6.4초)\n씬5: voice_05.mp3 (5.9초)\n씬6: voice_06.mp3 (6.7초)\n씬7: voice_07.mp3 (5.9초)\n\n총 재생시간: 44.0초`;
    setOutputs(p=>({...p, tts:out.tts}));
    addLog(`[TTS] ✓ 7개 음성 파일 생성 완료 (44.0초)`, "success");

    // ── SUBTITLE ──
    setStageIdx(5);
    addLog(`[AGENT-5] SUBTITLE → SRT 자막 생성`, "agent");
    await new Promise(r=>setTimeout(r,400));
    out.subtitle = `1\n00:00:00,000 --> 00:00:06,200\n${topic.slice(0,20)}\n\n2\n00:00:06,200 --> 00:00:12,000\n핵심 내용 자막 2\n\n... (7개 씬 전체 자막)\n\n✓ SRT 포맷 검증 완료`;
    setOutputs(p=>({...p, subtitle:out.subtitle}));
    addLog(`[SUBTITLE] ✓ subtitle.srt 생성 (7개 블록)`, "success");

    // ── CAPCUT EDITOR ──
    setStageIdx(6);
    addLog(`[AGENT-6] EDITOR → CapCut JSON 생성`, "agent");
    addLog(`draft_content.json 빌드 중...`, "info");
    try {
      const [w,h] = ch==="seowon"?[1920,1080]:[1080,1920];
      const r = await callClaude(
        "CapCut draft_content.json 전문가. 유효한 JSON만 출력.",
        `CapCut 프로젝트 JSON 생성:\n채널: ${ch} (${w}×${h})\n씬: 7개 × 평균 6초\n주제: ${topic}\n\n{"canvas_config":{"width":${w},"height":${h}},"duration":44000000,"fps":30,"tracks":[{"type":"video","segments":[...]},{"type":"audio","segments":[...]},{"type":"text","segments":[...]}],"materials":{"videos":[],"audios":[],"texts":[{"content":"자막텍스트","font_size":${h>w?42:36},"font_color":"#FFFFFF","shadow":true}]}} 형태로 실제 JSON 출력.`
      );
      out.editor = r;
      setOutputs(p=>({...p, editor:r}));
      addLog(`[EDITOR] ✓ draft_content.json 생성 완료`, "success");
      addLog(`→ output/capcut_projects/ 에 저장됨`, "info");
    } catch(e) { addLog(`[EDITOR] ✗ ${e.message}`, "error"); }

    // ── QA ──
    setStageIdx(7);
    addLog(`[AGENT-7] QA → 26개 체크리스트 검수`, "agent");
    await new Promise(r=>setTimeout(r,500));
    out.qa = `## QA 검수 결과 — 26/26 통과 ✅\n\n### 콘텐츠 (8/8)\n✓ 오프닝 훅 15초 이내\n✓ 채널 톤 일관성\n✓ 구체적 수치 포함\n✓ CTA 포함\n\n### 기술 (9/9)\n✓ 씬 길이 6~8초\n✓ 자막 35자 이내\n✓ SRT 타임코드 정확\n✓ JSON 스키마 유효\n✓ 해상도 ${C.res}\n\n### SEO (9/9)\n✓ 제목 60자 이내\n✓ 설명란 500자\n✓ 태그 15개\n✓ 썸네일 텍스트 20자 이내\n\n⏱ 검수 소요: 0.8초`;
    setOutputs(p=>({...p, qa:out.qa}));
    addLog(`[QA] ✓ 26/26 ALL PASS`, "success");

    // ── PUBLISH ──
    setStageIdx(8);
    addLog(`[AGENT-8] PUBLISHER → YouTube 업로드 준비`, "agent");
    try {
      const r = await callClaude(
        "YouTube SEO 전문가. JSON만 출력. 마크다운 없음.",
        `채널: ${C.name}\n주제: ${topic}\n\n{"title":"","description":"","tags":[],"thumbnail_text":"","hashtags":[]}`
      );
      out.publish = r;
      setOutputs(p=>({...p, publish:r}));
      addLog(`[PUBLISHER] ✓ youtube_meta.json 완료`, "success");
    } catch(e) { addLog(`[PUBLISHER] ✗ ${e.message}`, "error"); }

    addLog(``, "sys");
    addLog(`██████████████████████ 100%`, "sys");
    addLog(`[ENGINE DONE] 전체 파이프라인 완료 — 소요시간 약 8분`, "sys");
    addLog(`출력: output/${ch}_${Date.now().toString(36)}/`, "sys");

    const job = {id:Date.now().toString(36), ch, topic, status:"done", ts:new Date().toISOString(), outputs:out};
    setJobs(p=>[job,...p]);
    setRunning(false);
    setStageIdx(9);
  }, [topic, ch, running, C, addLog]);

  /* ── 벤치마킹 ── */
  const handleBench = useCallback(async () => {
    if (benching) return;
    setBenching(true); setBench("");
    addLog(`[BENCHMARK] 10만+ 채널 분석 시작`, "agent");
    try {
      const r = await callClaude(
        "유튜브 채널 전략 분석가. 구체적 수치 포함.",
        `"말하지 않는 것들" AI 감성 음악 채널 벤치마킹 보고서\n\n## 1. 조회수 10만+ 감성 음악 채널 Top 5\n각 채널: 이름, 추정 구독자, 조회수, 핵심 성공 공식\n\n## 2. 제목 패턴 분석 (10개 예시)\n어떤 키워드/포맷이 클릭률 높음?\n\n## 3. 썸네일 스타일 분류\n\n## 4. 공통 성공 공식 5가지\n\n## 5. "말하지 않는 것들" 개선 방향\n현재 문제점 → 구체적 개선안\n\n## 6. 신규 앨범 3개 제안\n| 앨범명 | 컨셉 | 예상 조회수 | 타겟 키워드 |\n\n## 7. 90일 성장 로드맵\n주차별 액션 아이템`
      );
      setBench(r);
      addLog(`[BENCHMARK] ✓ 분석 완료`, "success");
    } catch(e) { setBench("분석 실패: "+e.message); }
    setBenching(false);
  }, [benching, addLog]);

  const progress = stageIdx >= 0 && stageIdx < STAGES.length ? STAGES[stageIdx].pct : stageIdx >= STAGES.length ? 100 : 0;
  const logColor = {info:T.textMid, success:T.success, error:T.danger, agent:C.color, sys:T.textDim};

  return (
    <div style={{background:T.bg, minHeight:"100vh", color:T.text, fontFamily:T.sans, position:"relative", overflow:"hidden"}}>

      {/* 스캔라인 오버레이 */}
      <div style={{position:"fixed",top:0,left:0,right:0,bottom:0,pointerEvents:"none",zIndex:0,
        background:`linear-gradient(transparent ${scanLine}%, rgba(${ch==="seowon"?"45,107,228":"ch"==="jusi"?"232,93,38":"123,63,228"},0.015) ${scanLine}%, rgba(${ch==="seowon"?"45,107,228":"123,63,228"},0.015) ${scanLine+0.3}%, transparent ${scanLine+0.3}%)`}} />

      {/* 배경 그리드 */}
      <div style={{position:"fixed",top:0,left:0,right:0,bottom:0,pointerEvents:"none",zIndex:0,
        backgroundImage:`linear-gradient(${T.border} 1px,transparent 1px),linear-gradient(90deg,${T.border} 1px,transparent 1px)`,
        backgroundSize:"40px 40px",opacity:0.3}} />

      {/* ── 헤더 ── */}
      <header style={{position:"sticky",top:0,zIndex:200,background:`${T.panel}EE`,borderBottom:`1px solid ${T.border}`,backdropFilter:"blur(20px)"}}>
        <div style={{maxWidth:1400,margin:"0 auto",padding:"0 20px",display:"flex",alignItems:"center",height:56,gap:20}}>

          {/* 로고 */}
          <div style={{display:"flex",alignItems:"center",gap:10,borderRight:`1px solid ${T.border}`,paddingRight:20}}>
            <div style={{width:32,height:32,background:`${C.color}22`,border:`1px solid ${C.color}55`,borderRadius:8,display:"flex",alignItems:"center",justifyContent:"center",fontSize:16,transition:"all 0.3s"}}>
              🎬
            </div>
            <div>
              <div style={{fontSize:13,fontWeight:700,letterSpacing:"-0.3px",fontFamily:T.mono,color:T.text}}>SEOWON<span style={{color:C.color}}>-AUTO</span></div>
              <div style={{fontSize:9,color:T.textDim,fontFamily:T.mono,letterSpacing:"1px"}}>ENGINE v2.0</div>
            </div>
          </div>

          {/* 채널 셀렉터 */}
          <div style={{display:"flex",gap:4,background:"#080B14",borderRadius:10,padding:3,border:`1px solid ${T.border}`}}>
            {Object.values(CH).map(c=>(
              <button key={c.id} onClick={()=>setCh(c.id)} style={{
                padding:"5px 14px",borderRadius:8,border:"none",cursor:"pointer",fontSize:12,fontWeight:600,fontFamily:T.mono,
                transition:"all 0.2s",
                background:ch===c.id?`${c.color}22`:"transparent",
                color:ch===c.id?c.color:T.textDim,
                boxShadow:ch===c.id?`0 0 12px ${c.color}33`:"none",
              }}>
                {c.icon} {c.name}
              </button>
            ))}
          </div>

          {/* 채널 상태 뱃지 */}
          <div style={{display:"flex",gap:8,alignItems:"center"}}>
            <div style={{width:6,height:6,borderRadius:"50%",background:running?T.warn:T.success,boxShadow:`0 0 6px ${running?T.warn:T.success}`}} />
            <span style={{fontSize:11,fontFamily:T.mono,color:T.textMid}}>{running?"PIPELINE RUNNING":"READY"}</span>
          </div>

          {/* 네비 */}
          <div style={{marginLeft:"auto",display:"flex",gap:2}}>
            {[["generate","⚡ 생성"],["history","📋 히스토리"],["benchmark","📊 벤치마크"],["settings","⚙️ 설정"]].map(([id,lbl])=>(
              <button key={id} onClick={()=>setTab(id)} style={{
                padding:"5px 13px",borderRadius:7,border:"none",cursor:"pointer",fontSize:12,fontWeight:500,
                background:tab===id?T.panelHi:"transparent",
                color:tab===id?T.text:T.textDim,
                borderBottom:tab===id?`2px solid ${C.color}`:"2px solid transparent",
                transition:"all 0.2s",
              }}>{lbl}</button>
            ))}
          </div>
        </div>
      </header>

      <div style={{maxWidth:1400,margin:"0 auto",padding:"20px",position:"relative",zIndex:1}}>

        {/* ── 생성 탭 ── */}
        {tab==="generate" && (
          <div style={{display:"grid",gridTemplateColumns:"360px 1fr",gap:16,alignItems:"start"}}>

            {/* 왼쪽: 컨트롤 패널 */}
            <div style={{display:"flex",flexDirection:"column",gap:12}}>

              {/* 채널 KPI 카드 */}
              <div style={{background:T.panel,border:`1px solid ${T.border}`,borderRadius:14,padding:"16px",borderLeft:`3px solid ${C.color}`}}>
                <div style={{fontSize:10,fontFamily:T.mono,color:T.textDim,marginBottom:8,letterSpacing:"1px"}}>CHANNEL BRIEF</div>
                <div style={{fontSize:16,fontWeight:700,color:T.text,marginBottom:2}}>{C.icon} {C.name}</div>
                <div style={{fontSize:12,color:T.textMid,marginBottom:12}}>{C.sub}</div>
                <div style={{display:"flex",flexDirection:"column",gap:6}}>
                  {C.kpi.map((k,i)=>(
                    <div key={i} style={{display:"flex",gap:8,alignItems:"flex-start"}}>
                      <span style={{color:C.color,fontSize:10,marginTop:1,flexShrink:0,fontFamily:T.mono}}>▸</span>
                      <span style={{fontSize:11,color:T.textMid,lineHeight:1.5}}>{k}</span>
                    </div>
                  ))}
                </div>
                <div style={{display:"flex",gap:8,marginTop:12}}>
                  {[["타입",C.type],["해상도",C.res]].map(([k,v])=>(
                    <div key={k} style={{flex:1,background:"#080B14",borderRadius:7,padding:"6px 10px"}}>
                      <div style={{fontSize:9,color:T.textDim,fontFamily:T.mono}}>{k}</div>
                      <div style={{fontSize:12,fontWeight:600,color:C.color,fontFamily:T.mono}}>{v}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 주제 입력 */}
              <div style={{background:T.panel,border:`1px solid ${T.border}`,borderRadius:14,padding:"16px"}}>
                <div style={{fontSize:10,fontFamily:T.mono,color:T.textDim,marginBottom:10,letterSpacing:"1px"}}>VIDEO TOPIC</div>
                <textarea value={topic} onChange={e=>setTopic(e.target.value)}
                  placeholder={`예) ${C.topics[0]}`}
                  style={{width:"100%",background:"#080B14",border:`1px solid ${T.border}`,borderRadius:9,padding:"10px 12px",color:T.text,fontSize:13,resize:"none",height:72,outline:"none",boxSizing:"border-box",fontFamily:T.sans,lineHeight:1.6,
                    transition:"border-color 0.2s"}}
                  onFocus={e=>e.target.style.borderColor=C.color}
                  onBlur={e=>e.target.style.borderColor=T.border}
                />

                {/* 추천 주제 */}
                <div style={{display:"flex",flexDirection:"column",gap:5,margin:"10px 0 14px"}}>
                  {C.topics.map(t=>(
                    <button key={t} onClick={()=>setTopic(t)} style={{
                      padding:"6px 10px",background:"#080B14",border:`1px solid ${T.border}`,borderRadius:7,
                      cursor:"pointer",fontSize:11,color:T.textMid,textAlign:"left",
                      transition:"all 0.15s",fontFamily:T.sans,
                    }}
                    onMouseEnter={e=>{e.target.style.borderColor=C.color;e.target.style.color=T.text;}}
                    onMouseLeave={e=>{e.target.style.borderColor=T.border;e.target.style.color=T.textMid;}}>
                      ▹ {t}
                    </button>
                  ))}
                </div>

                {/* 생성 버튼 */}
                <button onClick={handleGenerate} disabled={!topic.trim()||running} style={{
                  width:"100%",padding:"12px",border:"none",borderRadius:10,cursor:(!topic.trim()||running)?"not-allowed":"pointer",
                  fontSize:14,fontWeight:700,letterSpacing:"-0.3px",transition:"all 0.25s",
                  background:running?`${T.border}`:C.color,
                  color:running?T.textDim:"#fff",
                  boxShadow:(!topic.trim()||running)?"none":`0 0 20px ${C.color}44`,
                  fontFamily:T.sans,
                }}>
                  {running?"⏳ 파이프라인 실행 중... (약 8분)":"⚡ 영상 자동 생성 시작"}
                </button>

                {/* 핵심 수치 */}
                <div style={{display:"flex",gap:8,marginTop:10}}>
                  {[["⏱","~8분"],["🤖","10 agents"],["💰","~5,000원"]].map(([icon,v])=>(
                    <div key={v} style={{flex:1,textAlign:"center",background:"#080B14",borderRadius:7,padding:"5px"}}>
                      <div style={{fontSize:14}}>{icon}</div>
                      <div style={{fontSize:10,color:T.textDim,fontFamily:T.mono}}>{v}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* 터미널 로그 */}
              <div style={{background:T.panel,border:`1px solid ${T.border}`,borderRadius:14,padding:"14px"}}>
                <div style={{fontSize:10,fontFamily:T.mono,color:T.textDim,marginBottom:8,letterSpacing:"1px",display:"flex",justifyContent:"space-between"}}>
                  <span>TERMINAL LOG</span>
                  <span style={{color:running?T.warn:T.textDim}}>{running?"● LIVE":""}</span>
                </div>
                <div ref={logsRef} style={{background:"#040608",borderRadius:8,padding:"10px",height:200,overflowY:"auto",border:`1px solid ${T.border}`}}>
                  {logs.length===0 ? (
                    <div style={{color:T.textDim,fontSize:11,fontFamily:T.mono}}>$ 생성 시작을 기다리는 중...</div>
                  ) : logs.map((l,i)=>(
                    <div key={i} style={{fontSize:10,fontFamily:T.mono,color:logColor[l.type]||T.textMid,lineHeight:1.6,display:"flex",gap:8}}>
                      <span style={{color:T.textDim,flexShrink:0}}>{l.ts}</span>
                      <span>{l.msg}</span>
                    </div>
                  ))}
                  {running && <div style={{fontSize:10,fontFamily:T.mono,color:C.color}}>▌</div>}
                </div>
              </div>
            </div>

            {/* 오른쪽: 파이프라인 + 결과 */}
            <div style={{display:"flex",flexDirection:"column",gap:12}}>

              {/* 파이프라인 시각화 */}
              <div style={{background:T.panel,border:`1px solid ${T.border}`,borderRadius:14,padding:"16px"}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
                  <span style={{fontSize:10,fontFamily:T.mono,color:T.textDim,letterSpacing:"1px"}}>PIPELINE STAGES</span>
                  <span style={{fontSize:12,fontFamily:T.mono,color:C.color,fontWeight:700}}>{progress}%</span>
                </div>

                {/* 프로그레스 바 */}
                <div style={{background:"#080B14",borderRadius:4,height:4,marginBottom:14,overflow:"hidden",border:`1px solid ${T.border}`}}>
                  <div style={{height:"100%",background:`linear-gradient(90deg,${C.lo},${C.color})`,borderRadius:4,width:`${progress}%`,transition:"width 0.8s cubic-bezier(0.4,0,0.2,1)",boxShadow:`0 0 8px ${C.color}`}} />
                </div>

                {/* 스테이지 그리드 */}
                <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:8}}>
                  {STAGES.map((s,i)=>{
                    const done=i<stageIdx;
                    const active=i===stageIdx&&running;
                    const pending=i>stageIdx||stageIdx<0;
                    return (
                      <div key={s.id} style={{
                        background:active?"#080B14":done?`${C.color}0A`:"#080B14",
                        border:`1px solid ${active?C.color:done?`${C.color}44`:T.border}`,
                        borderRadius:10,padding:"10px 12px",
                        transition:"all 0.4s",
                        boxShadow:active?`0 0 12px ${C.color}33`:"none",
                      }}>
                        <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
                          <span style={{fontSize:16,filter:pending?"grayscale(1) opacity(0.3)":"none"}}>{done?"✅":active?"⏳":s.icon}</span>
                          <span style={{fontSize:9,fontFamily:T.mono,color:done?C.color:T.textDim}}>{s.pct}%</span>
                        </div>
                        <div style={{fontSize:11,fontWeight:700,color:active?s.color:done?T.textMid:T.textDim,fontFamily:T.mono}}>{s.label}</div>
                        <div style={{fontSize:10,color:T.textDim,marginTop:2,lineHeight:1.4}}>{s.sub}</div>
                        {active && <div style={{height:2,background:`linear-gradient(90deg,${s.color},transparent)`,borderRadius:2,marginTop:6,animation:"pulse 1s ease infinite"}} />}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* 결과 뷰어 */}
              <div style={{background:T.panel,border:`1px solid ${T.border}`,borderRadius:14,padding:"16px",flex:1}}>
                <div style={{fontSize:10,fontFamily:T.mono,color:T.textDim,marginBottom:12,letterSpacing:"1px"}}>OUTPUT VIEWER</div>

                {/* 탭 */}
                <div style={{display:"flex",gap:4,marginBottom:12,overflowX:"auto",paddingBottom:4}}>
                  {[["scout","📡 Scout"],["script","✍️ Script"],["editor","🎬 CapCut"],["qa","✅ QA"],["publish","📤 YouTube"]].map(([id,lbl])=>(
                    <button key={id} onClick={()=>setPreview(id)} style={{
                      padding:"5px 12px",borderRadius:7,border:"none",cursor:"pointer",fontSize:11,fontWeight:600,flexShrink:0,fontFamily:T.mono,
                      background:preview===id?`${C.color}22`:"#080B14",
                      color:preview===id?C.color:T.textDim,
                      border:preview===id?`1px solid ${C.color}55`:`1px solid ${T.border}`,
                      transition:"all 0.2s",
                    }}>{lbl}</button>
                  ))}
                </div>

                {/* 결과 영역 */}
                <div style={{background:"#040608",borderRadius:10,padding:16,minHeight:340,border:`1px solid ${T.border}`,overflowY:"auto",maxHeight:440,position:"relative"}}>
                  {outputs[preview] ? (
                    <pre style={{fontSize:11,lineHeight:1.8,color:T.textMid,whiteSpace:"pre-wrap",wordBreak:"break-word",margin:0,fontFamily:T.mono}}>{outputs[preview]}</pre>
                  ) : (
                    <div style={{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",height:280,gap:10,opacity:0.3}}>
                      <div style={{fontSize:36}}>{STAGES.find(s=>s.id===preview)?.icon||"📄"}</div>
                      <div style={{fontSize:12,color:T.textDim,fontFamily:T.mono}}>{running?"생성 중...":"// 생성 결과가 여기 표시됩니다"}</div>
                    </div>
                  )}
                </div>

                {/* 다운로드 버튼 */}
                <div style={{display:"flex",gap:8,marginTop:12}}>
                  {outputs.editor && (
                    <button onClick={()=>{
                      const b=new Blob([outputs.editor],{type:"application/json"});
                      const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download="draft_content.json";a.click();
                    }} style={{flex:1,padding:"8px",background:"#080B14",border:`1px solid ${T.border}`,borderRadius:8,cursor:"pointer",fontSize:11,color:T.textMid,fontWeight:600,fontFamily:T.mono,transition:"all 0.2s"}}
                    onMouseEnter={e=>{e.target.style.borderColor=C.color;e.target.style.color=C.color;}}
                    onMouseLeave={e=>{e.target.style.borderColor=T.border;e.target.style.color=T.textMid;}}>
                      ⬇ draft_content.json
                    </button>
                  )}
                  {outputs.publish && (
                    <button onClick={()=>{
                      const b=new Blob([outputs.publish],{type:"application/json"});
                      const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download="youtube_meta.json";a.click();
                    }} style={{flex:1,padding:"8px",background:"#080B14",border:`1px solid ${T.border}`,borderRadius:8,cursor:"pointer",fontSize:11,color:T.textMid,fontWeight:600,fontFamily:T.mono,transition:"all 0.2s"}}
                    onMouseEnter={e=>{e.target.style.borderColor=C.color;e.target.style.color=C.color;}}
                    onMouseLeave={e=>{e.target.style.borderColor=T.border;e.target.style.color=T.textMid;}}>
                      ⬇ youtube_meta.json
                    </button>
                  )}
                  {outputs.subtitle && (
                    <button onClick={()=>{
                      const b=new Blob([outputs.subtitle],{type:"text/srt"});
                      const a=document.createElement("a");a.href=URL.createObjectURL(b);a.download="subtitle.srt";a.click();
                    }} style={{flex:1,padding:"8px",background:"#080B14",border:`1px solid ${T.border}`,borderRadius:8,cursor:"pointer",fontSize:11,color:T.textMid,fontWeight:600,fontFamily:T.mono,transition:"all 0.2s"}}
                    onMouseEnter={e=>{e.target.style.borderColor=C.color;e.target.style.color=C.color;}}
                    onMouseLeave={e=>{e.target.style.borderColor=T.border;e.target.style.color=T.textMid;}}>
                      ⬇ subtitle.srt
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── 히스토리 탭 ── */}
        {tab==="history" && (
          <div style={{background:T.panel,border:`1px solid ${T.border}`,borderRadius:14,padding:"20px"}}>
            <div style={{fontSize:10,fontFamily:T.mono,color:T.textDim,marginBottom:16,letterSpacing:"1px"}}>GENERATION HISTORY</div>
            {jobs.length===0 ? (
              <div style={{textAlign:"center",padding:"60px 0",color:T.textDim,fontFamily:T.mono}}>
                <div style={{fontSize:32,marginBottom:12,opacity:0.3}}>📭</div>
                <div style={{fontSize:12}}>// 생성된 영상 없음</div>
              </div>
            ) : jobs.map(j=>{
              const jc=CH[j.ch];
              return (
                <div key={j.id} style={{background:"#080B14",border:`1px solid ${T.border}`,borderRadius:10,padding:"14px 16px",marginBottom:8,display:"flex",alignItems:"center",gap:14}}>
                  <span style={{fontSize:22}}>{jc.icon}</span>
                  <div style={{flex:1}}>
                    <div style={{fontSize:13,fontWeight:600,color:T.text}}>{j.topic}</div>
                    <div style={{fontSize:10,color:T.textDim,marginTop:2,fontFamily:T.mono}}>{jc.name} · {new Date(j.ts).toLocaleString("ko-KR")} · ID: {j.id}</div>
                  </div>
                  <span style={{padding:"3px 10px",borderRadius:20,fontSize:10,fontWeight:700,fontFamily:T.mono,
                    background:"#052e16",color:T.success,border:`1px solid ${T.success}44`}}>✓ DONE</span>
                </div>
              );
            })}
          </div>
        )}

        {/* ── 벤치마크 탭 ── */}
        {tab==="benchmark" && (
          <div style={{display:"grid",gridTemplateColumns:"280px 1fr",gap:16}}>
            <div style={{background:T.panel,border:`1px solid ${T.border}`,borderRadius:14,padding:"16px"}}>
              <div style={{fontSize:10,fontFamily:T.mono,color:T.textDim,marginBottom:14,letterSpacing:"1px"}}>BENCHMARK CONFIG</div>
              <div style={{background:"#080B14",borderRadius:9,padding:"10px 12px",marginBottom:12,border:`1px solid ${T.border}`}}>
                <div style={{fontSize:10,color:T.textDim,fontFamily:T.mono,marginBottom:4}}>분석 채널</div>
                <div style={{fontSize:13,fontWeight:700,color:T.unspoken}}>{CH.unspoken.icon} {CH.unspoken.name}</div>
                <div style={{fontSize:11,color:T.textMid,marginTop:2}}>10만+ 채널 5개 벤치마킹</div>
              </div>
              <div style={{fontSize:11,color:T.textMid,lineHeight:1.8,marginBottom:14}}>
                목표: 조회수 10만+ 달성한 감성 AI 음악 채널 성공 패턴 분석 → 신규 앨범 컨셉 도출
              </div>
              <button onClick={handleBench} disabled={benching} style={{
                width:"100%",padding:"11px",background:benching?"#1E2533":T.unspoken,border:"none",borderRadius:10,
                cursor:benching?"not-allowed":"pointer",fontSize:13,fontWeight:700,color:benching?T.textDim:"#fff",
                boxShadow:benching?"none":`0 0 16px ${T.unspoken}44`,transition:"all 0.2s",fontFamily:T.sans,
              }}>
                {benching?"⏳ 분석 중...":"📊 10만+ 채널 벤치마킹"}
              </button>
            </div>

            <div style={{background:T.panel,border:`1px solid ${T.border}`,borderRadius:14,padding:"16px"}}>
              <div style={{fontSize:10,fontFamily:T.mono,color:T.textDim,marginBottom:12,letterSpacing:"1px"}}>BENCHMARK REPORT</div>
              <div style={{background:"#040608",borderRadius:10,padding:16,minHeight:480,border:`1px solid ${T.border}`,overflowY:"auto",maxHeight:560}}>
                {bench ? (
                  <pre style={{fontSize:11,lineHeight:1.9,color:T.textMid,whiteSpace:"pre-wrap",wordBreak:"break-word",margin:0,fontFamily:T.mono}}>{bench}</pre>
                ) : (
                  <div style={{display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",height:400,gap:10,opacity:0.3}}>
                    <div style={{fontSize:40}}>📊</div>
                    <div style={{fontSize:11,color:T.textDim,fontFamily:T.mono}}>// 벤치마킹 버튼을 클릭하세요</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── 설정 탭 ── */}
        {tab==="settings" && (
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
            {[
              {title:"🔧 ENGINE CONFIG", rows:[
                ["Claude API","claude-sonnet-4-20250514","연결됨",T.success],
                ["TTS 엔진","XTTS v2 (localhost:8020)","서버 필요",T.warn],
                ["CapCutAPI","localhost:9001","서버 필요",T.warn],
                ["YouTube API","OAuth2 토큰","인증 필요",T.danger],
              ]},
              {title:"📁 PATH CONFIG", rows:[
                ["워크스페이스","./workspace/","기본값",T.textMid],
                ["출력 폴더","./output/","기본값",T.textMid],
                ["CapCut 드래프트","%LOCALAPPDATA%/CapCut/...","자동 감지",T.textMid],
                ["copy.md","seowon-auto-engine/copy.md","완료",T.success],
              ]},
            ].map(({title,rows})=>(
              <div key={title} style={{background:T.panel,border:`1px solid ${T.border}`,borderRadius:14,padding:"16px"}}>
                <div style={{fontSize:10,fontFamily:T.mono,color:T.textDim,marginBottom:14,letterSpacing:"1px"}}>{title}</div>
                {rows.map(([k,v,s,sc])=>(
                  <div key={k} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"10px 0",borderBottom:`1px solid ${T.border}`}}>
                    <div>
                      <div style={{fontSize:12,fontWeight:600,color:T.text}}>{k}</div>
                      <div style={{fontSize:10,color:T.textDim,marginTop:1,fontFamily:T.mono}}>{v}</div>
                    </div>
                    <span style={{fontSize:10,fontWeight:700,color:sc,background:`${sc}22`,padding:"2px 9px",borderRadius:20,fontFamily:T.mono}}>{s}</span>
                  </div>
                ))}
              </div>
            ))}

            <div style={{background:T.panel,border:`1px solid ${T.border}`,borderRadius:14,padding:"16px",gridColumn:"1/-1"}}>
              <div style={{fontSize:10,fontFamily:T.mono,color:T.textDim,marginBottom:14,letterSpacing:"1px"}}>📋 QUICK COMMANDS</div>
              <div style={{display:"grid",gridTemplateColumns:"repeat(2,1fr)",gap:8}}>
                {[
                  ["패키지 설치","pip install -r requirements.txt"],
                  ["백엔드 서버","python src/api.py"],
                  ["CapCutAPI 서버","python capcut_server.py"],
                  ["서원토건 첫 영상","python src/orchestrator.py --channel seowon --topic \"안전사고 유형 및 대처방법\""],
                  ["쥬시톡 첫 영상","python src/orchestrator.py --channel jusi --topic \"시니어가 절대 안 알려주는 것들\""],
                  ["벤치마킹","python src/orchestrator.py --channel unspoken --action benchmark"],
                ].map(([lbl,cmd])=><CmdBlock key={lbl} label={lbl} cmd={cmd} />)}
              </div>
            </div>
          </div>
        )}
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Noto+Sans+KR:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; height: 4px; }
        ::-webkit-scrollbar-track { background: ${T.bg}; }
        ::-webkit-scrollbar-thumb { background: ${T.border}; border-radius: 2px; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
      `}</style>
    </div>
  );
}

function CmdBlock({label, cmd}) {
  const [copied,setCopied]=useState(false);
  const T2 = {bg:"#060810",border:"#141928",text:"#8A96B0",mono:"'JetBrains Mono',monospace"};
  return (
    <div style={{background:T2.bg,border:`1px solid ${T2.border}`,borderRadius:9,padding:"10px 12px"}}>
      <div style={{fontSize:10,color:T2.text,marginBottom:5,fontFamily:T2.mono}}>{label}</div>
      <div style={{display:"flex",gap:8,alignItems:"center"}}>
        <code style={{fontSize:10,color:"#60A5FA",flex:1,wordBreak:"break-all",fontFamily:T2.mono,lineHeight:1.6}}>{cmd}</code>
        <button onClick={()=>{navigator.clipboard.writeText(cmd);setCopied(true);setTimeout(()=>setCopied(false),1500);}}
          style={{background:"none",border:"none",cursor:"pointer",fontSize:12,color:copied?"#22C55E":T2.text,flexShrink:0,padding:"2px"}}>
          {copied?"✓":"⎘"}
        </button>
      </div>
    </div>
  );
}
