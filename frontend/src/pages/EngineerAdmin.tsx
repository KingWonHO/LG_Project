import { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useRole } from "@/context";
import { api, type TripCode, type Baseline } from "@/lib/api";
import { ShieldAlert, Plus, Loader2, Check, RefreshCw } from "lucide-react";

function SaveState({ state }: { state: string }) {
  if (state === "saving") return <span className="text-xs text-muted-foreground inline-flex items-center gap-1"><Loader2 className="h-3 w-3 animate-spin" /> 저장 중</span>;
  if (state === "saved") return <span className="text-xs text-emerald-600 inline-flex items-center gap-1"><Check className="h-3 w-3" /> 저장됨</span>;
  if (state) return <span className="text-xs text-destructive">{state}</span>;
  return null;
}

export default function EngineerAdmin() {
  const { role } = useRole();
  const [trips, setTrips] = useState<TripCode[]>([]);
  const [baselines, setBaselines] = useState<Baseline[]>([]);
  const [promptVer, setPromptVer] = useState("");
  const [promptText, setPromptText] = useState("");
  const [s, setS] = useState({ trip: "", base: "", prompt: "" });
  const [rag, setRag] = useState("");
  const [ragName, setRagName] = useState("");
  const [ragInterp, setRagInterp] = useState("");
  const [ragFile, setRagFile] = useState<File | null>(null);
  const [ragAdd, setRagAdd] = useState("");
  const [ragCount, setRagCount] = useState<number | null>(null);

  useEffect(() => {
    if (role !== "engineer") return;
    api.getTripCodes().then(setTrips).catch(() => {});
    api.getBaseline().then(setBaselines).catch(() => {});
    api.getPrompt().then((p) => { setPromptVer(p.version ?? ""); setPromptText(p.text); }).catch(() => {});
    api.engineerRulesStatus().then((r) => setRagCount(r.count)).catch(() => {});
  }, [role]);

  if (role !== "engineer") {
    return (
      <Card className="max-w-md">
        <CardContent className="pt-6 flex items-center gap-2 text-sm text-destructive">
          <ShieldAlert className="h-4 w-4" /> 엔지니어 권한이 필요합니다. 좌측 하단에서 엔지니어 로그인 후 이용하세요.
        </CardContent>
      </Card>
    );
  }

  const setTrip = (i: number, k: keyof TripCode, v: any) =>
    setTrips((p) => p.map((r, idx) => (idx === i ? { ...r, [k]: v } : r)));
  const addTrip = () =>
    setTrips((p) => [...p, { trip_no: 0, trip_key: "", trip_name_ko: "", summary_ko: "", restart_delay_s: null, solution: null }]);
  const saveTrips = async () => {
    setS((p) => ({ ...p, trip: "saving" }));
    try { await api.putTripCodes(trips); setS((p) => ({ ...p, trip: "saved" })); setTrips(await api.getTripCodes()); }
    catch (e: any) { setS((p) => ({ ...p, trip: "저장 실패: " + e.message })); }
  };

  const reindexRag = async () => {
    setRag("재인덱싱 중…");
    try { const r = await api.ragIndex(); setRag(`재인덱싱 완료 (${r.indexed}건)`); }
    catch (e: any) { setRag("재인덱싱 실패: " + e.message); }
  };
  const saveTripsAndReindex = async () => { await saveTrips(); await reindexRag(); };

  const setBase = (i: number, k: keyof Baseline, v: any) =>
    setBaselines((p) => p.map((r, idx) => (idx === i ? { ...r, [k]: v } : r)));
  const addBase = () =>
    setBaselines((p) => [...p, { feature_name: "", min_val: null, max_val: null, unit: null }]);
  const saveBase = async () => {
    setS((p) => ({ ...p, base: "saving" }));
    try { await api.putBaseline(baselines); setS((p) => ({ ...p, base: "saved" })); setBaselines(await api.getBaseline()); }
    catch (e: any) { setS((p) => ({ ...p, base: "저장 실패: " + e.message })); }
  };

  const savePrompt = async () => {
    setS((p) => ({ ...p, prompt: "saving" }));
    try { await api.putPrompt(promptVer || "v1", promptText); setS((p) => ({ ...p, prompt: "saved" })); }
    catch (e: any) { setS((p) => ({ ...p, prompt: "저장 실패: " + e.message })); }
  };

  const submitRagRule = async () => {
    if (!ragName || !ragInterp || !ragFile) { setRagAdd("룰 이름·해석·CSV를 모두 입력하세요."); return; }
    setRagAdd("등록 중…");
    try {
      const r = await api.addEngineerRule(ragName, ragInterp, ragFile);
      setRagAdd(`등록 완료 (판정 ${r.verdict}, 총 ${r.count}건)`);
      setRagCount(r.count);
      setRagName(""); setRagInterp(""); setRagFile(null);
    } catch (e: any) { setRagAdd("등록 실패: " + e.message); }
  };

  const numOrNull = (v: string) => (v === "" ? null : Number(v));

  return (
    <div className="space-y-4 max-w-4xl">
      <div>
        <h2 className="text-lg font-medium">엔지니어 관리</h2>
        <p className="text-sm text-muted-foreground">Trip Code · 정상 기준 · Prompt · RAG 룰 등록/수정 (백엔드 연동)</p>
      </div>

      <Tabs defaultValue="trip">
        <TabsList>
          <TabsTrigger value="trip">Trip Code</TabsTrigger>
          <TabsTrigger value="baseline">정상 기준</TabsTrigger>
          <TabsTrigger value="prompt">Prompt</TabsTrigger>
          <TabsTrigger value="ragrule">RAG 룰</TabsTrigger>
        </TabsList>

        <TabsContent value="trip">
          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle>Trip Code 등록/수정</CardTitle><SaveState state={s.trip} />
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b text-muted-foreground text-xs">
                    <th className="text-left py-2 font-normal w-16">No</th>
                    <th className="text-left py-2 font-normal">Key</th>
                    <th className="text-left py-2 font-normal">이름(ko)</th>
                    <th className="text-left py-2 font-normal">요약(ko)</th>
                    <th className="text-left py-2 font-normal w-24">재기동(s)</th>
                  </tr></thead>
                  <tbody>
                    {trips.map((t, i) => (
                      <tr key={i} className="border-b last:border-0">
                        <td className="py-1 pr-2"><Input value={t.trip_no} onChange={(e) => setTrip(i, "trip_no", Number(e.target.value))} /></td>
                        <td className="py-1 pr-2"><Input value={t.trip_key} onChange={(e) => setTrip(i, "trip_key", e.target.value)} /></td>
                        <td className="py-1 pr-2"><Input value={t.trip_name_ko} onChange={(e) => setTrip(i, "trip_name_ko", e.target.value)} /></td>
                        <td className="py-1 pr-2"><Input value={t.summary_ko} onChange={(e) => setTrip(i, "summary_ko", e.target.value)} /></td>
                        <td className="py-1"><Input value={t.restart_delay_s ?? ""} onChange={(e) => setTrip(i, "restart_delay_s", numOrNull(e.target.value))} /></td>
                      </tr>
                    ))}
                    {trips.length === 0 && <tr><td colSpan={5} className="py-4 text-center text-xs text-muted-foreground">데이터 없음</td></tr>}
                  </tbody>
                </table>
              </div>
              <div className="flex gap-2 items-center">
                <Button variant="outline" size="sm" onClick={addTrip}><Plus className="h-4 w-4" /> 행 추가</Button>
                <Button size="sm" onClick={saveTrips}>저장 (DB 반영)</Button>
                <Button variant="secondary" size="sm" onClick={saveTripsAndReindex}>
                  <RefreshCw className="h-4 w-4" /> 저장 + RAG 재인덱싱
                </Button>
                {rag && <span className="text-xs text-muted-foreground">{rag}</span>}
              </div>
              <p className="text-xs text-muted-foreground">
                Trip Code를 수정한 뒤 "RAG 재인덱싱"을 실행하면 리포트의 RAG 참고자료에 최신 내용이 반영됩니다.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="baseline">
          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle>정상 기준 등록/수정</CardTitle><SaveState state={s.base} />
            </CardHeader>
            <CardContent className="space-y-3">
              {baselines.map((b, i) => (
                <div key={i} className="grid grid-cols-[2fr_1fr_1fr_1fr] gap-2 items-center">
                  <Input placeholder="feature" value={b.feature_name} onChange={(e) => setBase(i, "feature_name", e.target.value)} />
                  <Input placeholder="min" value={b.min_val ?? ""} onChange={(e) => setBase(i, "min_val", numOrNull(e.target.value))} />
                  <Input placeholder="max" value={b.max_val ?? ""} onChange={(e) => setBase(i, "max_val", numOrNull(e.target.value))} />
                  <Input placeholder="unit" value={b.unit ?? ""} onChange={(e) => setBase(i, "unit", e.target.value || null)} />
                </div>
              ))}
              {baselines.length === 0 && <p className="text-xs text-muted-foreground">데이터 없음</p>}
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={addBase}><Plus className="h-4 w-4" /> 행 추가</Button>
                <Button size="sm" onClick={saveBase}>저장 (DB 반영)</Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="prompt">
          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle>Prompt 등록/수정</CardTitle><SaveState state={s.prompt} />
            </CardHeader>
            <CardContent className="space-y-2">
              <Input placeholder="버전 (예: v1)" value={promptVer} onChange={(e) => setPromptVer(e.target.value)} className="max-w-[200px]" />
              <textarea className="w-full h-48 rounded-md border bg-transparent p-3 text-sm" value={promptText} onChange={(e) => setPromptText(e.target.value)} />
              <Button size="sm" onClick={savePrompt}>저장 (DB 반영)</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ragrule">
          <Card>
            <CardHeader className="flex-row items-center justify-between space-y-0">
              <CardTitle>엔지니어 RAG 룰 추가</CardTitle>
              {ragCount !== null && <span className="text-xs text-muted-foreground">등록됨 {ragCount}건</span>}
            </CardHeader>
            <CardContent className="space-y-2">
              <p className="text-xs text-muted-foreground">
                대표 CSV와 해석 룰을 등록하면, 이후 <b>유사한 분석</b>에서 이 룰이 기존 Trip Code보다 우선 참고됩니다.
                (CSV를 분석한 판정·트립·이탈 시그니처로 유사도 판단)
              </p>
              <Input placeholder="룰 이름" value={ragName} onChange={(e) => setRagName(e.target.value)} className="max-w-[300px]" />
              <textarea className="w-full h-32 rounded-md border bg-transparent p-3 text-sm"
                        placeholder="해석/조치 내용 (자유서술)" value={ragInterp} onChange={(e) => setRagInterp(e.target.value)} />
              <input type="file" accept=".csv,.xlsx" onChange={(e) => setRagFile(e.target.files?.[0] ?? null)} className="text-sm" />
              <div className="flex gap-2 items-center">
                <Button size="sm" onClick={submitRagRule}><Plus className="h-4 w-4" /> 룰 + CSV 등록</Button>
                {ragAdd && <span className="text-xs text-muted-foreground">{ragAdd}</span>}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
