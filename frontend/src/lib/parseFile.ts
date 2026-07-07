import * as XLSX from "xlsx";
import { TIME_INDEX, TRIP_INDEX } from "./columnSchema";

export type ParsedFile = {
  columnCount: number;
  numericIndices: number[];        // 그릴 수 있는 숫자형 컬럼 인덱스 (1..19, Time/Trip 제외)
  rawNames: string[];              // 엑셀 원본 헤더명 (인덱스 기준, 참고용)
  rowCount: number;
  series: Record<string, number>[]; // { time, "1": v, "3": v, ... } 인덱스 문자열 키
  tripRanges: [number, number][];
  tripCount: number;
  tripCodes: number[];             // 실제 발생한 Trip_Code(idx20) 고유값 (0 제외)
};

export async function parseDataFile(file: File): Promise<ParsedFile> {
  const buf = await file.arrayBuffer();
  const wb = XLSX.read(buf, { type: "array" });
  const ws = wb.Sheets[wb.SheetNames[0]];
  const aoa = XLSX.utils.sheet_to_json<any[]>(ws, { header: 1, blankrows: false });

  // 헤더 행: 'time' 셀이 있는 행 (없으면 0행). 인덱스만 있는 행은 그 다음이 헤더가 됨.
  let hi = aoa.findIndex(
    (r) => Array.isArray(r) && r.some((c) => typeof c === "string" && c.trim().toLowerCase() === "time")
  );
  if (hi < 0) hi = 0;

  const header = (aoa[hi] as any[]) ?? [];
  const rawNames = header.map((c) => (c == null ? "" : String(c).trim()));
  const columnCount = rawNames.length;

  // 데이터 행 (위치 기준 — 빈 셀 필터로 인덱스가 밀리지 않도록 raw 배열을 그대로 사용)
  const dataRows: any[][] = [];
  for (let i = hi + 1; i < aoa.length; i++) {
    const r = aoa[i];
    if (!Array.isArray(r)) continue;
    if (r[TIME_INDEX] == null || r[TIME_INDEX] === "") continue;
    dataRows.push(r);
  }

  // 숫자형 컬럼 인덱스 판정 (1..19, Trip 제외) — 표본 100행 기준
  const maxIdx = Math.min(19, columnCount - 1);
  const sample = dataRows.slice(0, 100);
  const numericIndices: number[] = [];
  for (let idx = 1; idx <= maxIdx; idx++) {
    if (idx === TRIP_INDEX) continue;
    if (sample.some((r) => typeof r[idx] === "number" && Number.isFinite(r[idx]))) numericIndices.push(idx);
  }

  // Trip 구간 (인덱스 20 != 0 연속 구간)
  const tripRanges: [number, number][] = [];
  const codeSet = new Set<number>();
  let start: number | null = null;
  let prevT = 0;
  for (const r of dataRows) {
    const t = Number(r[TIME_INDEX]);
    const code = Number(r[TRIP_INDEX]) || 0;
    if (code !== 0) {
      codeSet.add(code);
      if (start == null) start = t;
    } else if (start != null) {
      tripRanges.push([start, prevT]);
      start = null;
    }
    prevT = t;
  }
  if (start != null) tripRanges.push([start, prevT]);
  const tripCodes = [...codeSet].sort((a, b) => a - b);

  // 다운샘플 + series (키: "time" + 인덱스 문자열)
  const step = Math.max(1, Math.ceil(dataRows.length / 2000));
  const series = dataRows
    .filter((_, i) => i % step === 0)
    .map((r) => {
      const s: Record<string, number> = { time: Number(r[TIME_INDEX]) };
      for (const idx of numericIndices) {
        const v = Number(r[idx]);
        s[String(idx)] = Number.isFinite(v) ? v : 0;
      }
      return s;
    });

  return { columnCount, numericIndices, rawNames, rowCount: dataRows.length, series, tripRanges, tripCount: tripRanges.length, tripCodes };
}

/**
 * xlsx/xls를 클라이언트(SheetJS)에서 CSV로 변환한 File을 반환한다.
 * 백엔드가 느린 openpyxl 대신 빠른 read_csv를 쓰도록, 업로드 전에 변환한다.
 * 이미 CSV면 원본을 그대로 반환.
 */
export async function toCsvFile(file: File): Promise<File> {
  const name = file.name.toLowerCase();
  if (!name.endsWith(".xlsx") && !name.endsWith(".xls")) return file;
  const buf = await file.arrayBuffer();
  const wb = XLSX.read(buf, { type: "array" });
  const ws = wb.Sheets[wb.SheetNames[0]];
  const csv = XLSX.utils.sheet_to_csv(ws);
  const base = file.name.replace(/\.(xlsx|xls)$/i, "");
  return new File([csv], `${base}.csv`, { type: "text/csv" });
}

export const LINE_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"];

/**
 * 1행짜리 트립처럼 x1===x2이거나 폭이 전체 시간 범위의 1% 미만이면 ReferenceArea가 안 보이므로,
 * 중심값 기준으로 전체 범위의 1.5%(1~2% 사이) 폭으로 확장한다.
 */
export function expandNarrowTripRanges(
  ranges: [number, number][],
  domainMin: number,
  domainMax: number,
): [number, number][] {
  const span = domainMax - domainMin;
  if (span <= 0) return ranges;
  const minWidth = span * 0.01;
  const expandedWidth = span * 0.015;
  return ranges.map(([a, b]) => {
    const width = b - a;
    if (width >= minWidth) return [a, b];
    const center = (a + b) / 2;
    return [center - expandedWidth / 2, center + expandedWidth / 2];
  });
}
