import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockHistory } from "@/lib/mock";

const badgeFor = (v: string) =>
  v === "PASS" ? "success" : v === "FAIL" ? "destructive" : "warning";

export default function History() {
  return (
    <div className="space-y-4 max-w-3xl">
      <div>
        <h2 className="text-lg font-medium">분석 이력</h2>
        <p className="text-sm text-muted-foreground">과거 업로드 파일과 분석 결과를 조회합니다. (ADM-002, 목업)</p>
      </div>
      <Card>
        <CardContent className="pt-4">
          <table className="w-full text-sm">
            <thead><tr className="border-b text-muted-foreground text-xs">
              <th className="text-left py-2 font-normal">일시</th>
              <th className="text-left py-2 font-normal">파일명</th>
              <th className="text-right py-2 font-normal">행 수</th>
              <th className="text-right py-2 font-normal">판정</th>
            </tr></thead>
            <tbody>
              {mockHistory.map((h) => (
                <tr key={h.파일명} className="border-b last:border-0">
                  <td className="py-2">{h.일시}</td>
                  <td className="py-2">{h.파일명}</td>
                  <td className="py-2 text-right">{h.행수.toLocaleString()}</td>
                  <td className="py-2 text-right"><Badge variant={badgeFor(h.판정) as any}>{h.판정}</Badge></td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
