import * as XLSX from "xlsx";

export type ParsedFile = {
  columns: string[];
  numericColumns: string[];
  rowCount: number;
  series: Record<string, number>[];   // 차트용(다운샘플), time + 숫자컬럼
  tripRanges: [number, number][];      // Trip_Code != 0 구간 (time 기준)
  tripCount: number;
};

// 업로드된 CSV/XLSX를 브라우저에서 파싱 (백엔드 비의존)
export async function parseDataFile(file: File): Promise<ParsedFile> {
  const buf = await file.arrayBuffer();
  const wb = XLSX.read(buf, { type: "array" });
  const ws = wb.Sheets[wb.SheetNames[0]];
  const aoa = XLSX.utils.sheet_to_json<any[]>(ws, { header: 1, blankrows: false });

  // 헤더 행 탐지: 'time' 이 들어있는 첫 행 (없으면 0행)
  let hi = aoa.findIndex(
    (r) => Array.isArray(r) && r.some((c) => typeof c === "string" && c.trim().toLowerCase() === "time")
  );
  if (hi < 0) hi = 0;

  const columns = (aoa[hi] as any[])
    .map((c) => (c == null ? "" : String(c).trim()))
    .filter((c) => c !== "");

  const rows: Record<string, any>[] = [];
  for (let i = hi + 1; i < aoa.length; i++) {
    const r = aoa[i];
    if (!Array.isArray(r)) continue;
    const o: Record<string, any> = {};
    columns.forEach((c, idx) => (o[c] = r[idx]));
    if (o["time"] == null || o["time"] === "") continue;
    rows.push(o);
  }

  // 숫자 컬럼 추출 (time/Trip_Code 제외)
  const numericColumns = columns.filter(
    (c) =>
      c !== "time" &&
      c !== "Trip_Code" &&
      rows.slice(0, 100).some((o) => typeof o[c] === "number" && Number.isFinite(o[c]))
  );

  // Trip_Code != 0 연속 구간
  const tripRanges: [number, number][] = [];
  let start: number | null = null;
  let prevT = 0;
  for (const o of rows) {
    const t = Number(o["time"]);
    const code = Number(o["Trip_Code"]) || 0;
    if (code !== 0) {
      if (start == null) start = t;
    } else if (start != null) {
      tripRanges.push([start, prevT]);
      start = null;
    }
    prevT = t;
  }
  if (start != null) tripRanges.push([start, prevT]);

  // 차트용 다운샘플 (최대 ~2000 포인트)
  const step = Math.max(1, Math.ceil(rows.length / 2000));
  const series = rows
    .filter((_, i) => i % step === 0)
    .map((o) => {
      const s: Record<string, number> = { time: Number(o["time"]) };
      for (const c of numericColumns) {
        const v = Number(o[c]);
        s[c] = Number.isFinite(v) ? v : 0;
      }
      return s;
    });

  return { columns, numericColumns, rowCount: rows.length, series, tripRanges, tripCount: tripRanges.length };
}

// 그래프 라인 색상 팔레트
export const LINE_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"];
