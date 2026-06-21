import { useRef, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea,
} from "recharts";
import { Upload, Play, Download, AlertTriangle, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { mockTimeseries, type Point } from "@/lib/mock";
import { api, type AnalyzeResponse } from "@/lib/api";
import { useApp } from "@/context";

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

export default function UserAnalysis() {
  const [file, setFile] = useState<File | null>(null);
  const [chart, setChart] = useState<Point[] | null>(null);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const { refreshHistory, setLastResult } = useApp();

  const verdict = result?.verdict ?? null;
  const tripRange: [number, number] | null =
    result && result.trip.ranges.length ? (result.trip.ranges[0] as [number, number]) : null;

  const run = async () => {
    if (!file) { setErr("CSV/XLSX 파일을 먼저 선택하세요."); return; }
    setLoading(true); setErr(null);
    try {
      const res = await api.analyze(file);
      setResult(res);
      setLastResult(res);
      setChart(mockTimeseries());            // TODO: 백엔드 series 연동 전 임시 차트
      await refreshHistory();                 // 좌측 이력 갱신
    } catch (e: any) {
      setErr("분석 실패: " + e.message + " (백엔드가 실행 중인지 확인)");
    } finally {
      setLoading(false);
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
        {/* 업로드 + 옵션 */}
        <Card>
          <CardContent className="pt-4 space-y-3">
            <div className="flex items-center gap-2">
              <Upload className="h-4 w-4 text-muted-foreground" />
              <input ref={fileRef} type="file" accept=".csv,.xlsx" className="hidden"
                     onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
              <button
                onClick={() => fileRef.current?.click()}
                className="flex-1 rounded-md border border-dashed px-3 py-2 text-center text-xs text-muted-foreground hover:bg-secondary/40"
              >
                {file ? file.name : "클릭하여 CSV / XLSX 파일 선택"}
              </button>
              <Button variant="outline" onClick={() => setChart(mockTimeseries())}>샘플 그래프</Button>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button onClick={run} disabled={loading}>
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />} 실행
              </Button>
              <Select defaultValue="all"><SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="all">컴프: 전체</SelectItem><SelectItem value="on">ON</SelectItem></SelectContent></Select>
              <Select defaultValue="all"><SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="all">전압: 전체</SelectItem><SelectItem value="rated">정격</SelectItem></SelectContent></Select>
              <Select defaultValue="all"><SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="all">RT: 전체</SelectItem><SelectItem value="rt1">RT1</SelectItem></SelectContent></Select>
              {err && <span className="ml-auto text-xs text-destructive">{err}</span>}
            </div>
          </CardContent>
        </Card>

        {/* 그래프 */}
        <Card className="flex flex-col h-[300px]">
          <CardHeader><CardTitle>그래프 <span className="text-xs text-muted-foreground">(series 백엔드 연동 전 임시)</span></CardTitle></CardHeader>
          <CardContent className="flex-1 min-h-0">
            {!chart ? (
              <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                실행 또는 '샘플 그래프' 후 표시됩니다.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chart} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="time" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  {tripRange && <ReferenceArea x1={tripRange[0]} x2={tripRange[1]} fill="#ef4444" fillOpacity={0.12} label="Trip" />}
                  <Line type="monotone" dataKey="컴프전류" stroke="#3b82f6" dot={false} />
                  <Line type="monotone" dataKey="전압" stroke="#10b981" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* 분석 결과 (실데이터, 챗 스타일) */}
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-base">분석 결과</CardTitle>
            <VerdictBadge verdict={verdict} />
          </CardHeader>
          <CardContent>
            {!result ? (
              <p className="text-sm text-muted-foreground py-6 text-center">실행 후 분석 결과가 여기에 표시됩니다.</p>
            ) : (
              <div className="flex gap-3">
                <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium shrink-0">AI</div>
                <div className="flex-1 rounded-lg border bg-muted/40 p-4 space-y-4 text-sm">
                  <p className="leading-relaxed">
                    <b>{result.filename}</b> 분석 결과, Trip이 <b>{result.trip.count}회</b>
                    {tripRange ? ` (구간 ${tripRange[0]}~${tripRange[1]})` : ""} 감지되었습니다.
                    {result.baseline.out_of_range.length > 0
                      ? ` baseline 이탈 항목: ${result.baseline.out_of_range.join(", ")}.`
                      : " baseline 이탈은 없습니다."}
                    {" "}데이터 품질에서 누락 {result.quality.missing}건, 이상치 {result.quality.outliers}건이 확인됩니다.
                    최종 판정은 <b>{result.verdict}</b>입니다.
                  </p>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[
                      ["Trip 발생", `${result.trip.count}회`],
                      ["baseline 이탈", result.baseline.out_of_range.join(", ") || "없음"],
                      ["데이터 품질", `이상치 ${result.quality.outliers}`],
                      ["판정", result.verdict],
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

        {/* 리포트 버튼 (맨 아래) */}
        <div className="flex gap-2">
          <Button variant="outline" className="flex-1"><Download className="h-4 w-4" /> 리포트 생성</Button>
          <Button variant="outline" className="flex-1" disabled={!result}>리포트 다운로드</Button>
        </div>
      </TabsContent>

      <TabsContent value="learning" className="mt-3">
        <Card><CardContent className="pt-6 text-sm text-muted-foreground">학습 기능은 목업 단계입니다.</CardContent></Card>
      </TabsContent>
    </Tabs>
  );
}
