import { useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Loader2, Download, AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import { api } from "@/lib/api";
import { useApp } from "@/context";

function VerdictBadge({ verdict }: { verdict: string }) {
  if (verdict === "PASS")
    return <Badge variant="success" className="text-sm px-3 py-1"><CheckCircle2 className="h-4 w-4" /> PASS</Badge>;
  if (verdict === "FAIL")
    return <Badge variant="destructive" className="text-sm px-3 py-1"><XCircle className="h-4 w-4" /> FAIL</Badge>;
  return <Badge variant="warning" className="text-sm px-3 py-1"><AlertTriangle className="h-4 w-4" /> {verdict}</Badge>;
}

export default function Report() {
  const { lastResult, reportData, setReportData } = useApp();
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = async () => {
    if (!lastResult) { setErr("먼저 '사용자 분석'에서 파일을 분석하세요."); return; }
    setLoading(true); setErr(null);
    try { setReportData(await api.report(lastResult)); }
    catch (e: any) { setErr("리포트 생성 실패: " + e.message); }
    finally { setLoading(false); }
  };

  const downloadMd = () => {
    if (!reportData) return;
    const md =
      `# 분석 리포트\n\n` +
      `- 파일: ${lastResult?.filename ?? "-"}\n` +
      `- 판정: ${lastResult?.verdict ?? "-"}\n` +
      `- Trip: ${lastResult?.trip.count ?? 0}회\n` +
      `- 모델: ${reportData.model ?? "-"}\n\n` +
      `## 요약\n\n${reportData.summary}\n`;
    const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `report_${(lastResult?.filename ?? "analysis").replace(/\.[^.]+$/, "")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-3xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-medium">리포트</h2>
          <p className="text-sm text-muted-foreground">로컬 LLM(Ollama)으로 분석 요약을 생성합니다. (LLM-001)</p>
        </div>
        {lastResult && <VerdictBadge verdict={lastResult.verdict} />}
      </div>

      {!lastResult ? (
        <Card><CardContent className="pt-6 text-sm text-muted-foreground">
          분석 결과가 없습니다. '사용자 분석'에서 파일을 분석한 뒤 이 화면에서 리포트를 생성하세요.
        </CardContent></Card>
      ) : (
        <>
          <Card>
            <CardContent className="pt-4 flex items-center justify-between gap-4">
              <p className="text-sm text-muted-foreground">
                대상: <b>{lastResult.filename}</b> · Trip {lastResult.trip.count}회 · 판정 {lastResult.verdict}
              </p>
              <div className="flex gap-2">
                <Button onClick={run} disabled={loading}>
                  {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                  {loading ? " 생성 중…" : reportData ? " 다시 생성" : " LLM 리포트 생성"}
                </Button>
                <Button variant="outline" onClick={downloadMd} disabled={!reportData}>
                  <Download className="h-4 w-4" /> 다운로드(.md)
                </Button>
              </div>
            </CardContent>
          </Card>

          {err && <p className="text-sm text-destructive">{err}</p>}

          {reportData && (
            <Card>
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <CardTitle>분석 요약</CardTitle>
                {reportData.model && <span className="text-xs text-muted-foreground">모델: {reportData.model}</span>}
              </CardHeader>
              <CardContent>
                <div className="flex gap-3">
                  <div className="h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-medium shrink-0">AI</div>
                  <div className="flex-1 rounded-lg border bg-muted/40 p-4 text-sm leading-relaxed whitespace-pre-wrap">
                    {reportData.summary}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
