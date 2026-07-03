import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea, Legend,
} from "recharts";
import { Upload, Play, FileText, AlertTriangle, CheckCircle2, XCircle, Loader2, Plus, Trash2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { parseDataFile, LINE_COLORS, expandNarrowTripRanges, type ParsedFile } from "@/lib/parseFile";
import { canonicalName, isPlottable, type PressureMode } from "@/lib/columnSchema";
import { api } from "@/lib/api";
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

// 기본 선택 컬럼: Imag(1)·DC_link(3)·Power(7) 우선, 없으면 앞에서 3개
function defaultCols(p: ParsedFile, mode: PressureMode): number[] {
  const plot = p.numericIndices.filter((i) => isPlottable(i, mode));
  const pref = [1, 3, 7].filter((i) => plot.includes(i));
  return pref.length ? pref : plot.slice(0, 3);
}

export default function UserAnalysis() {
  const { ua, setUa, refreshHistory, setLastResult } = useApp();
  const { file, parsed, mode, graphs, result } = ua;
  const navigate = useNavigate();

  const [parsing, setParsing] = useState(false);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const verdict = result?.verdict ?? null;
  const tripRanges = parsed
    ? expandNarrowTripRanges(parsed.tripRanges, parsed.series[0]?.time ?? 0, parsed.series[parsed.series.length - 1]?.time ?? 0)
    : [];
  const selectable = parsed ? parsed.numericIndices.filter((i) => isPlottable(i, mode)) : [];

  const onPick = async (f: File | null) => {
    setErr(null);
    setUa({ file: f, parsed: null, result: null, graphs: [[]] });
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
      const res = await api.analyze(file);
      setUa({ result: res });
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
        {/* 업로드 / 실행 */}
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
                행 {parsed.rowCount.toLocaleString()} · 컬럼 {parsed.columnCount} · Trip 구간 {parsed.tripCount}개 · 컬럼명 기준: <b>{mode}</b>(={mode === "차압" ? "DPS" : "NODPS"})
              </p>
            )}
            {err && <p className="text-xs text-destructive">{err}</p>}
          </CardContent>
        </Card>

        {/* 분석 결과 (위) */}
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
                    {file?.name && <b>{file.name}</b>} 파일에서 Trip 구간 <b>{parsed?.tripCount ?? 0}개</b>가 감지되었습니다.
                    {result ? <> 백엔드 판정 결과는 <b>{result.verdict}</b>입니다.</> : " (실행 시 백엔드 판정이 표시됩니다.)"}
                  </p>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[
                      ["Trip 구간(파일)", `${parsed?.tripCount ?? 0}개`],
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

        {/* 그래프 (아래, 여러 개) */}
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
          graphs.map((g, gi) => {
            const drawn = g.filter((i) => isPlottable(i, mode) && parsed.numericIndices.includes(i));
            return (
              <Card key={gi}>
                <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-base">그래프 {gi + 1} <span className="text-xs text-muted-foreground">· {drawn.length}개 컬럼</span></CardTitle>
                  {graphs.length > 1 && (
                    <Button variant="ghost" size="sm" onClick={() => removeGraph(gi)} className="text-muted-foreground hover:text-destructive">
                      <Trash2 className="h-4 w-4" /> 삭제
                    </Button>
                  )}
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex flex-wrap gap-1.5">
                    {selectable.map((idx) => (
                      <button key={idx} onClick={() => toggleCol(gi, idx)}
                        className={cn("rounded-md border px-2.5 py-1 text-xs transition-colors",
                          g.includes(idx) ? "bg-primary text-primary-foreground border-transparent" : "hover:bg-secondary/60")}>
                        {canonicalName(idx, mode)}
                      </button>
                    ))}
                  </div>
                  <div className="h-[300px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={parsed.series} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                        <XAxis dataKey="time" type="number" domain={["dataMin", "dataMax"]} tick={{ fontSize: 11 }} />
                        <YAxis tick={{ fontSize: 11 }} />
                        <Tooltip />
                        <Legend />
                        {tripRanges.map(([a, b], i) => (
                          <ReferenceArea key={i} x1={a} x2={b} fill="#ef4444" fillOpacity={0.12} />
                        ))}
                        {drawn.map((idx, i) => (
                          <Line key={idx} type="monotone" dataKey={String(idx)} name={canonicalName(idx, mode) ?? String(idx)}
                                stroke={LINE_COLORS[i % LINE_COLORS.length]} dot={false} strokeWidth={1.5} />
                        ))}
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </CardContent>
              </Card>
            );
          })
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
