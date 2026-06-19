import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea,
} from "recharts";
import { Upload, Play, Download, AlertTriangle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { mockTimeseries, mockResult, TRIP_RANGE, type Point } from "@/lib/mock";

export default function UserAnalysis() {
  const [data, setData] = useState<Point[] | null>(null);
  const [verdict, setVerdict] = useState<string | null>(null);

  const run = () => {
    if (!data) return;
    setVerdict("관리필요");
  };

  return (
    <Tabs defaultValue="analysis">
      <div className="flex items-center justify-between mb-4">
        <TabsList>
          <TabsTrigger value="analysis">분석</TabsTrigger>
          <TabsTrigger value="learning">학습</TabsTrigger>
        </TabsList>
        {verdict && (
          <Badge variant="warning"><AlertTriangle className="h-3.5 w-3.5" /> {verdict}</Badge>
        )}
      </div>

      <TabsContent value="analysis">
        <div className="grid grid-cols-1 lg:grid-cols-[1.6fr_1fr] gap-3">
          {/* 좌측 */}
          <div className="space-y-3">
            <Card>
              <CardHeader><CardTitle className="flex items-center gap-2"><Upload className="h-4 w-4" /> CSV / XLSX 업로드</CardTitle></CardHeader>
              <CardContent className="flex gap-2 items-center">
                <div className="flex-1 rounded-md border border-dashed px-3 py-3 text-center text-xs text-muted-foreground">
                  파일을 끌어다 놓기
                </div>
                <Button variant="outline" onClick={() => setData(mockTimeseries())}>샘플 불러오기</Button>
              </CardContent>
              {data && <p className="px-4 pb-3 text-xs text-muted-foreground">불러온 행 수: {data.length} · 컬럼: 4</p>}
            </Card>

            <Card>
              <CardContent className="pt-4 space-y-3">
                <div className="flex gap-2">
                  <Button onClick={run}><Play className="h-4 w-4" /> 실행</Button>
                  <Select defaultValue="all"><SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
                    <SelectContent><SelectItem value="all">컴프: 전체</SelectItem><SelectItem value="on">ON</SelectItem></SelectContent></Select>
                  <Select defaultValue="all"><SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
                    <SelectContent><SelectItem value="all">전압: 전체</SelectItem><SelectItem value="rated">정격</SelectItem></SelectContent></Select>
                  <Select defaultValue="all"><SelectTrigger className="w-28"><SelectValue /></SelectTrigger>
                    <SelectContent><SelectItem value="all">RT: 전체</SelectItem><SelectItem value="rt1">RT1</SelectItem></SelectContent></Select>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <Badge variant="secondary">컴프전류</Badge>
                  <Badge variant="secondary">전압</Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>그래프</CardTitle></CardHeader>
              <CardContent>
                {!data ? (
                  <p className="text-sm text-muted-foreground py-10 text-center">실행 전: 파일 업로드 후 그래프가 표시됩니다.</p>
                ) : (
                  <ResponsiveContainer width="100%" height={260}>
                    <LineChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                      <XAxis dataKey="time" tick={{ fontSize: 11 }} />
                      <YAxis tick={{ fontSize: 11 }} />
                      <Tooltip />
                      {verdict && <ReferenceArea x1={TRIP_RANGE[0]} x2={TRIP_RANGE[1]} fill="#ef4444" fillOpacity={0.12} />}
                      <Line type="monotone" dataKey="컴프전류" stroke="#3b82f6" dot={false} />
                      <Line type="monotone" dataKey="전압" stroke="#10b981" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </CardContent>
            </Card>
          </div>

          {/* 우측 */}
          <div className="space-y-3">
            <Card>
              <CardHeader><CardTitle>평압 / 차압</CardTitle></CardHeader>
              <CardContent>
                <Tabs defaultValue="평압">
                  <TabsList className="w-full"><TabsTrigger value="평압" className="flex-1">평압</TabsTrigger><TabsTrigger value="차압" className="flex-1">차압</TabsTrigger></TabsList>
                </Tabs>
              </CardContent>
            </Card>

            <Card className={verdict ? "bg-amber-50" : ""}>
              <CardContent className="pt-4 text-center">
                <p className="text-xs text-muted-foreground">Pass / Fail</p>
                <p className="text-2xl font-medium mt-1">{verdict ?? "-"}</p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>분석결과</CardTitle></CardHeader>
              <CardContent>
                {!verdict ? (
                  <p className="text-xs text-muted-foreground">아직 분석 결과가 없습니다.</p>
                ) : (
                  <table className="w-full text-xs">
                    <tbody>
                      {mockResult.map((r) => (
                        <tr key={r.항목} className="border-b last:border-0">
                          <td className="py-2 text-muted-foreground">{r.항목}</td>
                          <td className="py-2 text-right">{r.결과}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>리포트 출력</CardTitle></CardHeader>
              <CardContent>
                <Button variant="outline" className="w-full"><Download className="h-4 w-4" /> 리포트 생성 / 다운로드</Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </TabsContent>

      <TabsContent value="learning">
        <Card><CardContent className="pt-6 text-sm text-muted-foreground">학습 기능은 목업 단계입니다.</CardContent></Card>
      </TabsContent>
    </Tabs>
  );
}
