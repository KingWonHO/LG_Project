import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useRole } from "@/context";
import { mockTripCodes } from "@/lib/mock";
import { ShieldAlert, Database } from "lucide-react";

export default function EngineerAdmin() {
  const { role } = useRole();

  if (role !== "engineer") {
    return (
      <Card className="max-w-md">
        <CardContent className="pt-6 flex items-center gap-2 text-sm text-destructive">
          <ShieldAlert className="h-4 w-4" /> 엔지니어 권한이 필요합니다. 좌측에서 엔지니어 로그인 후 이용하세요.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4 max-w-4xl">
      <div>
        <h2 className="text-lg font-medium">엔지니어 관리</h2>
        <p className="text-sm text-muted-foreground">Trip Code · 정상 기준 · Rule · Prompt 등록/수정 및 DB 반영 (목업)</p>
      </div>

      <Tabs defaultValue="data">
        <TabsList>
          <TabsTrigger value="data">정상 데이터</TabsTrigger>
          <TabsTrigger value="trip">Trip Code</TabsTrigger>
          <TabsTrigger value="baseline">정상 기준</TabsTrigger>
          <TabsTrigger value="rule">Rule JSON</TabsTrigger>
          <TabsTrigger value="prompt">Prompt</TabsTrigger>
        </TabsList>

        <TabsContent value="data">
          <Card><CardHeader><CardTitle>정상 데이터 업로드 (ENG-001)</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-md border border-dashed px-3 py-4 text-center text-xs text-muted-foreground">baseline 생성용 정상 데이터 업로드</div>
              <div className="grid grid-cols-2 gap-2"><Input placeholder="모델명 예: COMP-A" /><Input placeholder="작성자 예: 송원호" /></div>
              <Button>baseline 생성</Button>
            </CardContent></Card>
        </TabsContent>

        <TabsContent value="trip">
          <Card><CardHeader><CardTitle>Trip Code 등록/수정 (ENG-002)</CardTitle></CardHeader>
            <CardContent>
              <table className="w-full text-sm">
                <thead><tr className="border-b text-muted-foreground text-xs">
                  <th className="text-left py-2 font-normal">Code</th><th className="text-left py-2 font-normal">의미</th>
                  <th className="text-left py-2 font-normal">원인</th><th className="text-left py-2 font-normal">조치</th></tr></thead>
                <tbody>{mockTripCodes.map((t) => (
                  <tr key={t.code} className="border-b last:border-0"><td className="py-2">{t.code}</td><td className="py-2">{t.의미}</td><td className="py-2">{t.원인}</td><td className="py-2">{t.조치}</td></tr>
                ))}</tbody>
              </table>
              <Button className="mt-3" variant="outline">Trip Code 저장</Button>
            </CardContent></Card>
        </TabsContent>

        <TabsContent value="baseline">
          <Card><CardHeader><CardTitle>정상 기준 등록/수정 (ENG-003)</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {[["Iqe", "0", "10"], ["CoolingPower", "50", "120"], ["Initial_Delay", "0", "5"]].map(([f, lo, hi]) => (
                <div key={f} className="grid grid-cols-[2fr_1fr_1fr] gap-2 items-center">
                  <span className="text-sm font-medium">{f}</span>
                  <Input defaultValue={lo} /><Input defaultValue={hi} />
                </div>
              ))}
              <Button variant="outline">정상 기준 저장</Button>
            </CardContent></Card>
        </TabsContent>

        <TabsContent value="rule">
          <Card><CardHeader><CardTitle>Rule JSON 등록/수정 (ENG-004)</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <textarea className="w-full h-48 rounded-md border bg-transparent p-3 text-xs font-mono" defaultValue={'{\n  "rules": [\n    { "feature": "CoolingPower", "op": ">", "value": 120, "verdict": "관리필요" }\n  ]\n}'} />
              <div className="flex gap-2"><Button variant="outline">형식 검증</Button><Button variant="outline">Rule 저장</Button></div>
            </CardContent></Card>
        </TabsContent>

        <TabsContent value="prompt">
          <Card><CardHeader><CardTitle>Prompt 등록/수정 (ENG-005)</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              <textarea className="w-full h-40 rounded-md border bg-transparent p-3 text-sm" defaultValue={"다음 분석 결과를 바탕으로 요약/원인/조치를 작성하라:\n{analysis_json}"} />
              <Button variant="outline">Prompt 저장</Button>
            </CardContent></Card>
        </TabsContent>
      </Tabs>

      <Button><Database className="h-4 w-4" /> DB 반영 (ENG-006)</Button>
    </div>
  );
}
