import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea, Legend, Brush,
} from "recharts";
import { Upload, Play, FileText, AlertTriangle, CheckCircle2, XCircle, Loader2, Plus, Trash2, Send, BookmarkPlus } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { parseDataFile, LINE_COLORS, expandNarrowTripRanges, type ParsedFile } from "@/lib/parseFile";
import { canonicalName, isPlottable, isNoise, type PressureMode } from "@/lib/columnSchema";
import { api, type CompressorsData, type AnalyzeResponse, type ChatMsg } from "@/lib/api";
import { useApp } from "@/context";
import { cn } from "@/lib/utils";

function VerdictBadge({ verdict }: { verdict: string | null }) {
  if (verdict === "PASS")
    return <Badge variant="success" className="text-sm px-3 py-1"><CheckCircle2 className="h-4 w-4" /> PASS</Badge>;
  if (verdict === "FAIL")
    return <Badge variant="destructive" className="text-sm px-3 py-1"><XCircle className="h-4 w-4" /> FAIL</Badge>;
  if (verdict === "관리필요")
    return <Badge variant="warning" className="text-sm px-3 py-1"><AlertTriangle className="h-4 w-4" /> 관리필요</Badge>;
  if (verdict) return <Badge variant="secondary" className="text-sm px-3 py-1">{verdict}</Badge>;
  return <Badge variant="secondary" className="text-sm px-3 py-1">분석 전</Badge>;
}

function defaultCols(p: ParsedFile, mode: PressureMode): number[] {
  const plot = p.numericIndices.filter((i) => isPlottable(i, mode));
  const pref = [1, 3, 7].filter((i) => plot.includes(i));
  return pref.length ? pref : plot.slice(0, 3);
}

// 분석 결과 컨텍스트 기반 LLM 대화 + 대화 결과 학습 DB 반영
function ChatPanel({ analysis }: { analysis: AnalyzeResponse }) {
  const { ua, setUa } = useApp();
  const chat = ua.chat;
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [learnMsg, setLearnMsg] = useState("");

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    const next: ChatMsg[] = [...chat, { role: "user", content: text }];
    setUa({ chat: next });
    setInput("");
    setSending(true);
    try {
      const r = await api.chat(analysis, next);
      setUa({ chat: [...next, { role: "assistant", content: r.reply }] });
    } catch (e: any) {
      setUa({ chat: [...next, { role: "assistant", content: "오류: " + e.message }] });
    } finally {
      setSending(false);
    }
  };

  const learn = async (content: string) => {
    setLearnMsg("반영 중…");
    try {
      const r = await api.learn(analysis, content);
      setLearnMsg(`학습 DB 반영 완료 (총 ${r.count}건)`);
    } catch (e: any) {
      setLearnMsg("반영 실패: " + e.message);
    }
  };

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base">LLM 대화</CardTitle>
        {chat.length > 0 && (
          <Button variant="ghost" size="sm" className="h-7 text-xs text-muted-foreground" onClick={() => setUa({ chat: [] })}>대화 초기화</Button>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="max-h-80 overflow-y-auto space-y-2 pr-1">
          {chat.length === 0 && (
            <p className="text-xs text-muted-foreground">분석 결과에 대해 질문하세요. 예) "이 판정의 원인은?", "관리필요 이유 설명", "우선 점검 항목은?"</p>
          )}
          {chat.map((m, i) => (
            <div key={i} className={cn("flex gap-2", m.role === "user" ? "justify-end" : "")}>
              {m.role === "assistant" && <div className="h-6 w-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-[10px] font-medium shrink-0">AI</div>}
              <div className={cn("rounded-lg px-3 py-2 text-sm max-w-[80%] whitespace-pre-wrap", m.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted/50 border")}>
                {m.content}
                {m.role === "assistant" && (
                  <div className="mt-1">
                    <Button variant="ghost" size="sm" className="h-6 px-1 text-[11px] text-muted-foreground" onClick={() => learn(m.content)}>
                      <BookmarkPlus className="h-3 w-3" /> 학습 DB에 반영
                    </Button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
        {learnMsg && <p className="text-xs text-muted-foreground">{learnMsg}</p>}
        <div className="flex gap-2">
          <Input value={input} onChange={(e) => setInput(e.target.value)}
                 onKeyDown={(e) => e.key === "Enter" && send()} placeholder="질문 입력…" disabled={sending} />
          <Button onClick={send} disabled={sending || !input.trim()}>
            {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

type GraphCardProps = {
  parsed: ParsedFile;
  mode: PressureMode;
  tripRanges: [number, number][];
  cols: number[];
  selectable: number[];
  index: number;
  canRemove: boolean;
  onToggle: (idx: number) => void;
  onRemove: () => void;
};

function GraphCard({ parsed, mode, tripRanges, cols, selectable, index, canRemove, onToggle, onRemove }: GraphCardProps) {
  const drawn = cols.filter((i) => isPlottable(i, mode) && parsed.numericIndices.includes(i));
  const len = parsed.series.length;

  const [range, setRange] = useState<[number, number]>([0, Math.max(0, len - 1)]);
  useEffect(() => { setRange([0, Math.max(0, len - 1)]); }, [len]);

  const timeAt = (i: number) => parsed.series[Math.min(Math.max(i, 0), len - 1)]?.time ?? 0;
  const startTime = timeAt(range[0]);
  const endTime = timeAt(range[1]);

  const [inS, setInS] = useState("");
  const [inE, setInE] = useState("");
  const [yMax, setYMax] = useState("");
  useEffect(() => { setInS(String(Math.round(startTime))); setInE(String(Math.round(endTime))); }, [startTime, endTime]);

  const yMaxNum = yMax !== "" && Number.isFinite(Number(yMax)) ? Number(yMax) : null;

  const applyTime = () => {
    const s = Number(inS), e = Number(inE);
    if (!Number.isFinite(s) || !Number.isFinite(e) || s >= e) return;
    let si = parsed.series.findIndex((p) => p.time >= s);
    if (si < 0) si = 0;
    let ei = len - 1;
    for (let i = len - 1; i >= 0; i--) { if (parsed.series[i].time <= e) { ei = i; break; } }
    if (ei <= si) ei = Math.min(len - 1, si + 1);
    setRange([si, ei]);
  };
  const resetRange = () => setRange([0, Math.max(0, len - 1)]);

  // 노이즈 전처리: 정상범위(엔지니어 스펙)를 벗어난 값을 그래프에서 제거(null)
  const [cleanNoise, setCleanNoise] = useState(true);
  const chartData = useMemo<Record<string, number | null>[]>(() => {
    const dr = cols.filter((i) => isPlottable(i, mode) && parsed.numericIndices.includes(i));
    if (!cleanNoise || dr.length === 0) return parsed.series;
    return parsed.series.map((row) => {
      let out: Record<string, number | null> = row;
      for (const idx of dr) {
        const v = row[String(idx)];
        if (typeof v === "number" && isNoise(idx, mode, v)) {
          out = out === row ? { ...row } : out;
          out[String(idx)] = null;
        }
      }
      return out;
    });
  }, [parsed.series, parsed.numericIndices, cols, mode, cleanNoise]);

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base">그래프 {index + 1} <span className="text-xs text-muted-foreground">· {drawn.length}개 컬럼</span></CardTitle>
        {canRemove && (
          <Button variant="ghost" size="sm" onClick={onRemove} className="text-muted-foreground hover:text-destructive">
            <Trash2 className="h-4 w-4" /> 삭제
          </Button>
        )}
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex flex-wrap gap-1.5">
          {selectable.map((idx) => (
            <button key={idx} onClick={() => onToggle(idx)}
              className={cn("rounded-md border px-2.5 py-1 text-xs transition-colors",
                cols.includes(idx) ? "bg-primary text-primary-foreground border-transparent" : "hover:bg-secondary/60")}>
              {canonicalName(idx, mode)}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-muted-foreground shrink-0">시간 구간</span>
          <Input type="number" value={inS} onChange={(e) => setInS(e.target.value)}
                 onKeyDown={(e) => e.key === "Enter" && applyTime()} className="h-7 w-28" />
          <span className="text-muted-foreground">~</span>
          <Input type="number" value={inE} onChange={(e) => setInE(e.target.value)}
                 onKeyDown={(e) => e.key === "Enter" && applyTime()} className="h-7 w-28" />
          <Button size="sm" variant="outline" className="h-7" onClick={applyTime}>적용</Button>
          <Button size="sm" variant="ghost" className="h-7" onClick={resetRange}>리셋</Button>
          <span className="text-muted-foreground shrink-0 ml-2">Y축 최대</span>
          <Input type="number" value={yMax} onChange={(e) => setYMax(e.target.value)} placeholder="auto" className="h-7 w-24" />
          <Button size="sm" variant={cleanNoise ? "secondary" : "ghost"} className="h-7 ml-2"
                  onClick={() => setCleanNoise((v) => !v)} title="정상범위 초과 값을 노이즈로 보고 제거">
            노이즈 제거 {cleanNoise ? "ON" : "OFF"}
          </Button>
        </div>

        <div className="h-[300px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
              <XAxis dataKey="time" type="number" domain={["dataMin", "dataMax"]} tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} domain={[0, yMaxNum ?? "auto"]} allowDataOverflow={yMaxNum !== null} />
              <Tooltip />
              <Legend />
              {tripRanges.map(([a, b], i) => (
                <ReferenceArea key={i} x1={a} x2={b} fill="#ef4444" fillOpacity={0.12} />
              ))}
              {drawn.map((idx, i) => (
                <Line key={idx} type="monotone" dataKey={String(idx)} name={canonicalName(idx, mode) ?? String(idx)}
                      stroke={LINE_COLORS[i % LINE_COLORS.length]} dot={false} strokeWidth={1.5} isAnimationActive={false} />
              ))}
              <Brush dataKey="time" height={18} stroke="#94a3b8" travellerWidth={8}
                     startIndex={range[0]} endIndex={range[1]}
                     onChange={(r: any) => {
                       if (!r || typeof r.startIndex !== "number" || typeof r.endIndex !== "number") return;
                       setRange((prev) => (prev[0] === r.startIndex && prev[1] === r.endIndex ? prev : [r.startIndex, r.endIndex]));
                     }}
                     tickFormatter={(t) => String(t)} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

export default function UserAnalysis() {
  const { ua, setUa, refreshHistory, setLastResult } = useApp();
  const { file, parsed, mode, compModel, graphs, result } = ua;
  const navigate = useNavigate();

  const [parsing, setParsing] = useState(false);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [tripNames, setTripNames] = useState<Record<number, string>>({});
  const [compData, setCompData] = useState<CompressorsData>({ models: [], definitions: {}, compressors: {} });
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    api.getTripCodes()
      .then((list) => {
        const m: Record<number, string> = {};
        for (const t of list) m[t.trip_no] = t.trip_name_ko;
        setTripNames(m);
      })
      .catch(() => {});
    api.getCompressors().then(setCompData).catch(() => {});
  }, []);

  const compParams = compModel ? compData.compressors[compModel]?.parameters : undefined;

  const verdict = result?.verdict ?? null;
  // Trip 수/구간은 백엔드 판정(result) 우선, 실행 전에는 프론트 파싱값(예상)
  const tripCountShown = result ? result.trip.count : (parsed?.tripCount ?? 0);
  const tripRangesShown: [number, number][] = result
    ? (result.trip.ranges as [number, number][])
    : (parsed?.tripRanges ?? []);
  const tripRanges = parsed
    ? expandNarrowTripRanges(parsed.tripRanges, parsed.series[0]?.time ?? 0, parsed.series[parsed.series.length - 1]?.time ?? 0)
    : [];
  const selectable = parsed ? parsed.numericIndices.filter((i) => isPlottable(i, mode)) : [];

  const onPick = async (f: File | null) => {
    setErr(null);
    setUa({ file: f, parsed: null, result: null, graphs: [[]], chat: [] });
    if (!f) return;
    setParsing(true);
    try {
      const p = await parseDataFile(f);
      setUa({ parsed: p, graphs: [defaultCols(p, mode)] });
    } catch (e: any) {
      setErr("파일 파싱 실패: " + e.message);
    } finally {
      setParsing(false);
    }
  };

  const setMode = (m: PressureMode) => setUa({ mode: m });

  const toggleCol = (gi: number, idx: number) =>
    setUa({
      graphs: graphs.map((g, i) =>
        i === gi ? (g.includes(idx) ? g.filter((x) => x !== idx) : [...g, idx]) : g
      ),
    });
  const addGraph = () => setUa({ graphs: [...graphs, parsed ? defaultCols(parsed, mode) : []] });
  const removeGraph = (gi: number) => setUa({ graphs: graphs.filter((_, i) => i !== gi) });

  const run = async () => {
    if (!file) { setErr("CSV/XLSX 파일을 먼저 선택하세요."); return; }
    setRunning(true); setErr(null);
    try {
      // 원본 파일을 그대로 전송 (백엔드가 calamine으로 빠르게 파싱). 클라이언트 변환은 메인스레드를 얼려서 제거함.
      const res = await api.analyze(file, compModel || undefined);
      setUa({ result: res, chat: [] });
      setLastResult(res);
      await refreshHistory();
    } catch (e: any) {
      setErr("분석 실패: " + e.message + " (백엔드 실행 확인)");
    } finally {
      setRunning(false);
    }
  };

  return (
    <Tabs defaultValue="analysis">
      <div className="flex items-center justify-between gap-4">
        <TabsList>
          <TabsTrigger value="analysis">분석</TabsTrigger>
          <TabsTrigger value="learning">학습</TabsTrigger>
        </TabsList>
        <div className="flex items-center gap-3">
          <Select value={compModel || undefined} onValueChange={(v) => setUa({ compModel: v })}>
            <SelectTrigger className="h-9 w-[150px]"><SelectValue placeholder="컴프 모델 선택" /></SelectTrigger>
            <SelectContent>
              {compData.models.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
            </SelectContent>
          </Select>
          <Tabs value={mode} onValueChange={(v) => setMode(v as PressureMode)}>
            <TabsList>
              <TabsTrigger value="평압">평압</TabsTrigger>
              <TabsTrigger value="차압">차압</TabsTrigger>
            </TabsList>
          </Tabs>
          <VerdictBadge verdict={verdict} />
        </div>
      </div>

      <TabsContent value="analysis" className="space-y-3 mt-3">
        <Card>
          <CardContent className="pt-4 space-y-3">
            <div className="flex items-center gap-2">
              <Upload className="h-4 w-4 text-muted-foreground" />
              <input ref={fileRef} type="file" accept=".csv,.xlsx" className="hidden"
                     onChange={(e) => onPick(e.target.files?.[0] ?? null)} />
              <button onClick={() => fileRef.current?.click()}
                className="flex-1 rounded-md border border-dashed px-3 py-2 text-center text-xs text-muted-foreground hover:bg-secondary/40">
                {file ? file.name : "클릭하여 CSV / XLSX 파일 선택"}
              </button>
              <Button onClick={run} disabled={running || parsing || !file}>
                {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />} 실행
              </Button>
            </div>

            {parsing && <p className="text-xs text-muted-foreground inline-flex items-center gap-1"><Loader2 className="h-3 w-3 animate-spin" /> 파일 파싱 중…</p>}
            {parsed && (
              <p className="text-xs text-muted-foreground">
                행 {parsed.rowCount.toLocaleString()} · 컬럼 {parsed.columnCount} · Trip 구간 {tripCountShown}개{result ? "(백엔드)" : "(분석 전)"} · 컬럼명 기준: <b>{mode}</b>(={mode === "차압" ? "DPS" : "NODPS"})
              </p>
            )}
            {err && <p className="text-xs text-destructive">{err}</p>}
          </CardContent>
        </Card>

        {compParams && (
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-base">모델 파라미터 · {compModel}</CardTitle></CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
                {Object.entries(compParams).map(([k, v]) => (
                  <div key={k} className="rounded-md border bg-muted/30 p-2">
                    <p className="text-[11px] text-muted-foreground truncate" title={compData.definitions[k]?.display_name_ko ?? k}>
                      {compData.definitions[k]?.display_name_ko ?? k}
                    </p>
                    <p className="text-sm font-medium">
                      {v ?? "-"}{v != null && compData.definitions[k]?.unit ? ` ${compData.definitions[k]?.unit}` : ""}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* 분석 결과 */}
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-base">분석 결과</CardTitle>
            <VerdictBadge verdict={verdict} />
          </CardHeader>
          <CardContent>
            {!result && !parsed ? (
              <p className="text-sm text-muted-foreground py-6 text-center">실행 후 분석 결과가 표시됩니다.</p>
            ) : (
              <div className="flex gap-3">
                <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium shrink-0">AI</div>
                <div className="flex-1 rounded-lg border bg-muted/40 p-4 space-y-4 text-sm">
                  <p className="leading-relaxed">
                    {file?.name && <b>{file.name}</b>} 파일에서 Trip 구간 <b>{tripCountShown}개</b>가 감지되었습니다.
                    {result ? <> 백엔드 판정 결과는 <b>{result.verdict}</b>입니다.</> : " (실행 시 백엔드 판정이 표시됩니다.)"}
                  </p>
                  {parsed && (
                    <p className="text-xs leading-relaxed">
                      <span className="text-muted-foreground">발생 Trip Code: </span>
                      {parsed.tripCodes.length === 0
                        ? "없음"
                        : parsed.tripCodes.map((c) => (tripNames[c] ? `${c} · ${tripNames[c]}` : `${c}`)).join(",  ")}
                    </p>
                  )}
                  {tripRangesShown.length > 0 && (
                    <p className="text-xs leading-relaxed">
                      <span className="text-muted-foreground">트립 발생 시간(구간): </span>
                      {tripRangesShown.map(([a, b]) => (a === b ? `${a}` : `${a}~${b}`)).join(",  ")}
                    </p>
                  )}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[
                      ["Trip 구간(백엔드)", result ? `${result.trip.count}개` : "-"],
                      ["행 수", parsed ? parsed.rowCount.toLocaleString() : "-"],
                      ["판정(백엔드)", result?.verdict ?? "-"],
                      ["이상치(백엔드)", result ? String(result.quality.outliers) : "-"],
                    ].map(([k, v]) => (
                      <div key={k} className="rounded-md bg-background border p-2.5">
                        <p className="text-xs text-muted-foreground">{k}</p>
                        <p className="text-sm font-medium mt-0.5">{v}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* LLM 대화 (분석 실행 후) */}
        {result && <ChatPanel analysis={result} />}

        {/* 그래프 */}
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-medium">그래프</h3>
          <Button variant="outline" size="sm" onClick={addGraph} disabled={!parsed}>
            <Plus className="h-4 w-4" /> 그래프 추가
          </Button>
        </div>

        {!parsed ? (
          <Card><CardContent className="pt-6 text-sm text-muted-foreground text-center">
            파일을 선택하면 실제 시계열 그래프가 표시됩니다.
          </CardContent></Card>
        ) : (
          graphs.map((g, gi) => (
            <GraphCard
              key={gi}
              parsed={parsed}
              mode={mode}
              tripRanges={tripRanges}
              cols={g}
              selectable={selectable}
              index={gi}
              canRemove={graphs.length > 1}
              onToggle={(idx) => toggleCol(gi, idx)}
              onRemove={() => removeGraph(gi)}
            />
          ))
        )}

        <div className="flex gap-2">
          <Button className="flex-1" disabled={!result} onClick={() => navigate("/report")}>
            <FileText className="h-4 w-4" /> 리포트 생성·보기
          </Button>
        </div>
      </TabsContent>

      <TabsContent value="learning" className="mt-3">
        <Card><CardContent className="pt-6 text-sm text-muted-foreground">
          학습 기능은 추후 제공 예정입니다. (정상 baseline 학습/갱신)
        </CardContent></Card>
      </TabsContent>
    </Tabs>
  );
}
