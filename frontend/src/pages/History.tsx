import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { useApp } from "@/context";

function VerdictBadge({ verdict }: { verdict: string }) {
  const v = verdict === "PASS" ? "success" : verdict === "FAIL" ? "destructive" : "warning";
  return <Badge variant={v as any} className="text-sm px-3 py-1">{verdict}</Badge>;
}

export default function History() {
  const { history, selectedId } = useApp();
  const rec = history.find((h) => h.id === selectedId) ?? history[0];

  if (!rec) {
    return (
      <div className="max-w-3xl">
        <h2 className="text-lg font-medium mb-2">분석 이력</h2>
        <Card><CardContent className="pt-6 text-sm text-muted-foreground">
          분석 기록이 없습니다. '사용자 분석'에서 분석을 실행하면 좌측 이력에 쌓입니다.
        </CardContent></Card>
      </div>
    );
  }

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">{rec.filename}</h2>
          <p className="text-sm text-muted-foreground">{rec.time}</p>
        </div>
        <VerdictBadge verdict={rec.verdict} />
      </div>

      {/* 챗/프롬프트 스타일 결과 */}
      <Card>
        <CardHeader><CardTitle>분석 결과</CardTitle></CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium shrink-0">AI</div>
            <div className="flex-1 rounded-lg border bg-muted/40 p-4 space-y-4 text-sm">
              <p className="leading-relaxed">{rec.narrative}</p>
              <table className="w-full text-sm">
                <tbody>
                  {rec.result.map((r) => (
                    <tr key={r.항목} className="border-b last:border-0">
                      <td className="py-2 text-muted-foreground">{r.항목}</td>
                      <td className="py-2 text-right font-medium">{r.결과}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <Button variant="outline" className="flex-1"><Download className="h-4 w-4" /> 리포트 생성</Button>
        <Button variant="outline" className="flex-1">리포트 다운로드</Button>
      </div>
    </div>
  );
}
