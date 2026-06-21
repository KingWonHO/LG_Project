import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useApp } from "@/context";

function VerdictBadge({ verdict }: { verdict: string }) {
  const v = verdict === "PASS" ? "success" : verdict === "FAIL" ? "destructive" : "warning";
  return <Badge variant={v as any} className="text-sm px-3 py-1">{verdict}</Badge>;
}

export default function History() {
  const { history, selected } = useApp();
  const rec = selected ?? history[0];

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

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">{rec.파일명}</h2>
          <p className="text-sm text-muted-foreground">{rec.일시}{rec.행수 != null ? ` · ${rec.행수.toLocaleString()}행` : ""}</p>
        </div>
        <VerdictBadge verdict={rec.판정} />
      </div>
      <Card>
        <CardContent className="pt-6 text-sm space-y-2">
          <p className="text-muted-foreground">
            분석 이력 요약입니다. 상세 결과(서술·원인·조치)는 백엔드 상세 조회 엔드포인트(<code>GET /api/history/&#123;id&#125;</code>) 추가 후 연결됩니다.
          </p>
          <table className="w-full">
            <tbody>
              <tr className="border-b"><td className="py-2 text-muted-foreground">파일명</td><td className="py-2 text-right font-medium">{rec.파일명}</td></tr>
              <tr className="border-b"><td className="py-2 text-muted-foreground">일시</td><td className="py-2 text-right">{rec.일시}</td></tr>
              <tr className="border-b"><td className="py-2 text-muted-foreground">행 수</td><td className="py-2 text-right">{rec.행수 ?? "-"}</td></tr>
              <tr><td className="py-2 text-muted-foreground">판정</td><td className="py-2 text-right font-medium">{rec.판정}</td></tr>
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
