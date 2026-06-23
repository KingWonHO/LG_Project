import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea, Legend,
} from "recharts";
import { Upload, Play, FileText, AlertTriangle, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { parseDataFile, LINE_COLORS } from "@/lib/parseFile";
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

const PREFERRED = ["Iqe", "CoolingPower", "Power", "DC_Link", "Ide", "Initial_Delay"];

export default function UserAnalysis() {
  const { ua, setUa, refreshHistory, setLastResult } = useApp();
  const { file, parsed, cols, result } = ua;
  const navigate = useNavigate();

  const [parsing, setParsing] = useState(false);
  const [running, setRunning] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const verdict = result?.verdict ?? null;

  const onPick = async (f: File | null) => {
    setErr(null);
    setUa({ file: f, parsed: null, result: null, cols: [] });
    if (!f) return;
    setParsing(true);
    try {
      const p = await parseDataFile(f);
      const def = PREFERRED.filter((c) => p.numericColumns.includes(c));
      setUa({ parsed: p, cols: def.length ? def.slice(0, 3) : p.numericColumns.slice(0, 3) });
    } catch (e: any) {
      setErr("파일 파싱 실패: " + e.message);
    } finally {
      setParsing(false);
    }
  };

  const toggleCol = (c: string) =>
    setUa({ cols: cols.includes(c) ? cols.filter((x) => x !== c) : [...cols, c] });

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
          <Tabs defaultValue="평압">
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
                행 {parsed.rowCount.toLocaleString()} · 컬럼 {parsed.columns.length} · Trip 구간 {parsed.tripCount}개
              </p>
            )}

            {parsed && (
              <div className="flex flex-wrap gap-1.5">
                {parsed.numericColumns.map((c) => (
                  <button key={c} onClick={() => toggleCol(c)}
                    className={cn("rounded-md border px-2.5 py-1 text-xs transition-colors",
                      cols.includes(c) ? "bg-primary text-primary-foreground border-transparent" : "hover:bg-secondary/60")}>
                    {c}
                  </button>
                ))}
              </div>
            )}
            {err && <p className="text-xs text-destructive">{err}</p>}
          </CardContent>
        </Card>

        <Card className="flex flex-col h-[340px]">
          <CardHeader><CardTitle>그래프 {parsed && <span className="text-xs text-muted-foreground">· 실제 데이터 ({cols.length}개 컬럼)</span>}</CardTitle></CardHeader>
          <CardContent className="flex-1 min-h-0">
            {!parsed ? (
              <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                파일을 선택하면 실제 시계열 그래프가 표시됩니다.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={parsed.series} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="time" type="number" domain={["dataMin", "dataMax"]} tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  {parsed.tripRanges.map(([a, b], i) => (
                    <ReferenceArea key={i} x1={a} x2={b} fill="#ef4444" fillOpacity={0.12} />
                  ))}
                  {cols.map((c, i) => (
                    <Line key={c} type="monotone" dataKey={c} stroke={LINE_COLORS[i % LINE_COLORS.length]} dot={false} strokeWidth={1.5} />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

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
