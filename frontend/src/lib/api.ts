// 백엔드 REST 클라이언트. dev는 vite 프록시(/api→8000), prod는 nginx 프록시.
const BASE = "/api";

async function j<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

// /api/analyze 응답 (main.py 실측)
export type AnalyzeResponse = {
  verdict: string;
  trip: { count: number; ranges: number[][] };
  baseline: { out_of_range: string[] };
  quality: { missing: number; outliers: number };
  filename: string;
  file_id: number;
  result_id: number;
};

export type HistoryItem = { 일시: string; 파일명: string; 행수: number | null; 판정: string };

export type TripCode = {
  trip_no: number;
  trip_key: string;
  trip_name_ko: string;
  summary_ko: string;
  restart_delay_s: number | null;
  solution: Record<string, unknown> | null;
  updated_at?: string;
};

export type Baseline = {
  feature_name: string;
  min_val: number | null;
  max_val: number | null;
  unit: string | null;
  updated_at?: string;
};

export type PromptData = { version: string | null; text: string };

export type ReportData = { summary: string; model?: string };

const jsonHeaders = { "Content-Type": "application/json" };

export const api = {
  health: () => fetch(`${BASE}/health`).then(j<{ status: string; llm_model: string }>),

  analyze: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetch(`${BASE}/analyze`, { method: "POST", body: fd }).then(j<AnalyzeResponse>);
  },

  history: () => fetch(`${BASE}/history`).then(j<HistoryItem[]>),

  // 엔지니어 관리
  getTripCodes: () => fetch(`${BASE}/trip-codes`).then(j<TripCode[]>),
  putTripCodes: (items: TripCode[]) =>
    fetch(`${BASE}/trip-codes`, { method: "PUT", headers: jsonHeaders, body: JSON.stringify(items) }).then(j<{ saved: number }>),

  getBaseline: () => fetch(`${BASE}/baseline`).then(j<Baseline[]>),
  putBaseline: (items: Baseline[]) =>
    fetch(`${BASE}/baseline`, { method: "PUT", headers: jsonHeaders, body: JSON.stringify(items) }).then(j<{ saved: number }>),

  getPrompt: () => fetch(`${BASE}/prompt`).then(j<PromptData>),
  putPrompt: (version: string, text: string) =>
    fetch(`${BASE}/prompt`, { method: "PUT", headers: jsonHeaders, body: JSON.stringify({ version, text }) }).then(j<{ ok: boolean }>),

  putRules: (rules: unknown) =>
    fetch(`${BASE}/rules`, { method: "PUT", headers: jsonHeaders, body: JSON.stringify(rules) }).then(j<{ ok: boolean }>),

  // 리포트 (다음 단계)
  report: (analysis: unknown) =>
    fetch(`${BASE}/report`, { method: "POST", headers: jsonHeaders, body: JSON.stringify(analysis) }).then(j<ReportData>),
};
