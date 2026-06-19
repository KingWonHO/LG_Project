import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

export default function Report() {
  return (
    <div className="space-y-4 max-w-3xl">
      <div>
        <h2 className="text-lg font-medium">리포트</h2>
        <p className="text-sm text-muted-foreground">분석 요약 · Trip 분석 · 이상 항목 · 원인 후보 · 조치 권고 (목업)</p>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[["최종 판정", "관리필요"], ["Trip 발생", "3회"], ["이상 항목", "2건"]].map(([k, v]) => (
          <Card key={k}><CardContent className="pt-4"><p className="text-xs text-muted-foreground">{k}</p><p className="text-xl font-medium mt-1">{v}</p></CardContent></Card>
        ))}
      </div>

      <Card>
        <CardHeader><CardTitle>분석 요약</CardTitle></CardHeader>
        <CardContent className="text-sm">
          업로드 데이터에서 Trip 3회(구간 150~172)가 감지되었고, CoolingPower가 정상 baseline 상한을 초과하여 관리필요로 판정되었습니다.
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>원인 후보 (LLM-002)</CardTitle></CardHeader>
        <CardContent className="text-sm space-y-1">
          <p>· 냉매 부족 가능성 — CoolingPower 저하 패턴</p>
          <p>· 컴프 과부하 — Trip 구간 전류 급증</p>
          <p>· 센서 노이즈 — 일부 구간 이상치</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>조치 권고 (LLM-003)</CardTitle></CardHeader>
        <CardContent className="text-sm space-y-1">
          <p>· 냉매 충전량 점검</p>
          <p>· 컴프 전류 파형 재측정</p>
          <p>· 해당 RT 센서 캘리브레이션</p>
        </CardContent>
      </Card>

      <Button variant="outline"><Download className="h-4 w-4" /> 리포트 다운로드 (목업)</Button>
    </div>
  );
}
