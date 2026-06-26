import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea, Legend,
} from "recharts";
import { Loader2 } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useApp } from "@/context";
import { api, type HistoryDetail } from "@/lib/api";
import { LINE_COLORS, expandNarrowTripRanges } from "@/lib/parseFile";

function VerdictBadge({ verdict }: { verdict: string }) {
  const v = verdict === "PASS" ? "success" : verdict === "FAIL" ? "destructive" : "warning";
  return <Badge variant={v as any} className="text-sm px-3 py-1">{verdict}</Badge>;
}

export default function History() {
  const { history, selected } = useApp();
  const rec = selected ?? history[0];

  const [detail, setDetail] = useState<HistoryDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setDetail(null);
    if (!rec) return;
    setLoading(true);
    setErr(null);
    api.historyDetail(rec.result_id)
      .then(setDetail)
      .catch((e) => setErr("상세 결과를 불러오지 못했습니다: " + e.message))
      .finally(() => setLoading(false));
  }, [rec?.result_id]);

  if (!rec) {
    return (
      <div className="max-w-3xl">
        <h2 className="text-lg font-medium mb-2">분석 이력</h2>
        <Card><CardContent className="pt-6 text-sm text-muted-foreground">
          분석 기록이 없습니다. '사용자 분석'에서 파일을 분석하면 좌측 이력에 쌓입니다.
        </CardContent></Card>
      </div>
    );
  }

  const seriesCols = detail ? Object.keys(detail.series[0] ?? {}).filter((c) => c !== "time") : [];
  const tripRanges = detail
    ? expandNarrowTripRanges(
        detail.trip.ranges as [number, number][],
        detail.series[0]?.time ?? 0,
        detail.series[detail.series.length - 1]?.time ?? 0,
      )
    : [];

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">{rec.파일명}</h2>
          <p className="text-sm text-muted-foreground">{rec.일시}{rec.행수 != null ? ` · ${rec.행수.toLocaleString()}행` : ""}</p>
        </div>
        <VerdictBadge verdict={rec.판정} />
      </div>

      <Card className="flex flex-col h-[340px]">
        <CardHeader><CardTitle>그래프</CardTitle></CardHeader>
        <CardContent className="flex-1 min-h-0">
          {loading ? (
            <div className="h-full flex items-center justify-center text-sm text-muted-foreground gap-1">
              <Loader2 className="h-4 w-4 animate-spin" /> 불러오는 중…
            </div>
          ) : err ? (
            <p className="text-sm text-destructive">{err}</p>
          ) : !detail ? (
            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
              그래프를 불러올 수 없습니다.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={detail.series} margin={{ top: 8, right: 8, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="time" type="number" domain={["dataMin", "dataMax"]} tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                {tripRanges.map(([a, b], i) => (
                  <ReferenceArea key={i} x1={a} x2={b} fill="#ef4444" fillOpacity={0.12} />
                ))}
                {seriesCols.map((c, i) => (
                  <Line key={c} type="monotone" dataKey={c} stroke={LINE_COLORS[i % LINE_COLORS.length]} dot={false} strokeWidth={1.5} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">분석 결과</CardTitle></CardHeader>
        <CardContent>
          <table className="w-full text-sm">
            <tbody>
              <tr className="border-b"><td className="py-2 text-muted-foreground">파일명</td><td className="py-2 text-right font-medium">{rec.파일명}</td></tr>
              <tr className="border-b"><td className="py-2 text-muted-foreground">일시</td><td className="py-2 text-right">{rec.일시}</td></tr>
              <tr className="border-b"><td className="py-2 text-muted-foreground">행 수</td><td className="py-2 text-right">{rec.행수 ?? "-"}</td></tr>
              <tr className="border-b"><td className="py-2 text-muted-foreground">판정</td><td className="py-2 text-right font-medium">{rec.판정}</td></tr>
              <tr className="border-b"><td className="py-2 text-muted-foreground">Trip 발생</td><td className="py-2 text-right">{detail ? `${detail.trip.count}회` : "-"}</td></tr>
              <tr className="border-b"><td className="py-2 text-muted-foreground">baseline 이탈</td>
                <td className="py-2 text-right">{detail ? (detail.baseline.out_of_range.length ? detail.baseline.out_of_range.join(", ") : "없음") : "-"}</td></tr>
              <tr><td className="py-2 text-muted-foreground">데이터 품질</td>
                <td className="py-2 text-right">{detail ? `누락 ${detail.quality.missing}건 · 이상치 ${detail.quality.outliers}건` : "-"}</td></tr>
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
