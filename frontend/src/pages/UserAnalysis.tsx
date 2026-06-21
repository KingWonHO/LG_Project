import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea,
} from "recharts";
import { Upload, Play, Download, AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { mockTimeseries, mockResult, TRIP_RANGE, type Point } from "@/lib/mock";
import { useApp, type AnalysisRecord } from "@/context";

function VerdictBadge({ verdict }: { verdict: string | null }) {
  if (verdict === "PASS")
    return <Badge variant="success" className="text-sm px-3 py-1"><CheckCircle2 className="h-4 w-4" /> PASS</Badge>;
  if (verdict === "FAIL")
    return <Badge variant="destructive" className="text-sm px-3 py-1"><XCircle className="h-4 w-4" /> FAIL</Badge>;
  if (verdict === "관리필요")
    return <Badge variant="warning" className="text-sm px-3 py-1"><AlertTriangle className="h-4 w-4" /> 관리필요</Badge>;
  return <Badge variant="secondary" className="text-sm px-3 py-1">분석 전</Badge>;
}

export default function UserAnalysis() {
  const [data, setData] = useState<Point[] | null>(null);
  const [verdict, setVerdict] = useState<string | null>(null);
  const { addRecord } = useApp();

  const run = () => {
    if (!data) return;
    setVerdict("관리필요");
    const rec: AnalysisRecord = {
      id: Date.now().toString(),
      filename: "comp_sample.csv",
      time: new Date().toLocaleString("ko-KR"),
      verdict: "관리필요",
      trip: "Trip 3회",
      narrative:
        "업로드 데이터에서 Trip이 3회(구간 150~172) 감지되었습니다. CoolingPower가 정상 baseline 상한을 초과하여 '관리필요'로 판정했습니다. 데이터 품질에서 이상치 2건이 확인됩니다.",
      result: mockResult,
    };
    addRecord(rec);
  };

  return (
    <Tabs defaultValue="analysis">
      {/* 헤더 */}
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
              <div className="flex-1 rounded-md border border-dashed px-3 py-2 text-center text-xs text-muted-foreground">
                CSV / XLSX 파일을 끌어다 놓기
              </div>
              <Button variant="outline" onClick={() => setData(mockTimeseries())}>샘플 불러오기</Button>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button onClick={run}><Play className="h-4 w-4" /> 실행</Button>
              <Select defaultValue="all"><SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="all">컴프: 전체</SelectItem><SelectItem value="on">ON</SelectItem></SelectContent></Select>
              <Select defaultValue="all"><SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="all">전압: 전체</SelectItem><SelectItem value="rated">정격</SelectItem></SelectContent></Select>
              <Select defaultValue="all"><SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
                <SelectContent><SelectItem value="all">RT: 전체</SelectItem><SelectItem value="rt1">RT1</SelectItem></SelectContent></Select>
              <div className="flex gap-1.5 ml-1">
                <Badge variant="secondary">컴프전류</Badge>
                <Badge variant="secondary">전압</Badge>
              </div>
              {data && <span className="ml-auto text-xs text-muted-foreground">행 {data.length} · 컬럼 4</span>}
            </div>
          </CardContent>
        </Card>

        {/* 그래프 */}
        <Card className="flex flex-col h-[300px]">
          <CardHeader><CardTitle>그래프</CardTitle></CardHeader>
          <CardContent className="flex-1 min-h-0">
            {!data ? (
              <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
                파일 업로드 후 그래프가 표시됩니다.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                  <XAxis dataKey="time" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  {verdict && <ReferenceArea x1={TRIP_RANGE[0]} x2={TRIP_RANGE[1]} fill="#ef4444" fillOpacity={0.12} label="Trip" />}
                  <Line type="monotone" dataKey="컴프전류" stroke="#3b82f6" dot={false} />
                  <Line type="monotone" dataKey="전압" stroke="#10b981" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </CardContent>
        </Card>

        {/* 분석 결과 (그래프 아래, 챗/프롬프트 스타일) */}
        <Card>
          <CardHeader className="flex-row items-center justify-between space-y-0">
            <CardTitle className="text-base">분석 결과</CardTitle>
            <VerdictBadge verdict={verdict} />
          </CardHeader>
          <CardContent>
            {!verdict ? (
              <p className="text-sm text-muted-foreground py-6 text-center">
                실행 후 분석 결과가 여기에 표시됩니다.
              </p>
            ) : (
              <div className="flex gap-3">
                <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium shrink-0">AI</div>
                <div className="flex-1 rounded-lg border bg-muted/40 p-4 space-y-4 text-sm">
                  <p className="leading-relaxed">
                    업로드 데이터에서 <b>Trip이 3회(구간 150~172)</b> 감지되었습니다.
                    <b> CoolingPower</b>가 정상 baseline 상한을 초과하여 <b>관리필요</b>로 판정했습니다.
                    데이터 품질에서 이상치 2건이 확인됩니다.
                  </p>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {[["Trip 발생", "3회"], ["baseline 이탈", "CoolingPower"], ["데이터 품질", "이상치 2"], ["판정", "관리필요"]].map(([k, v]) => (
                      <div key={k} className="rounded-md bg-background border p-2.5">
                        <p className="text-xs text-muted-foreground">{k}</p>
                        <p className="text-sm font-medium mt-0.5">{v}</p>
                      </div>
                    ))}
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    <Badge variant="warning">CoolingPower 초과</Badge>
                    <Badge variant="secondary">Trip 구간 150~172</Badge>
                    <Badge variant="secondary">이상치 2건</Badge>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* 리포트 버튼 (맨 아래 줄) */}
        <div className="flex gap-2">
          <Button variant="outline" className="flex-1"><Download className="h-4 w-4" /> 리포트 생성</Button>
          <Button variant="outline" className="flex-1" disabled={!verdict}>리포트 다운로드</Button>
        </div>
      </TabsContent>

      <TabsContent value="learning" className="mt-3">
        <Card><CardContent className="pt-6 text-sm text-muted-foreground">학습 기능은 목업 단계입니다.</CardContent></Card>
      </TabsContent>
    </Tabs>
  );
}
