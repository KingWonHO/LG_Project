import * as XLSX from "xlsx";

export type ParsedFile = {
  columns: string[];
  numericColumns: string[];
  rowCount: number;
  series: Record<string, number>[];
  tripRanges: [number, number][];
  tripCount: number;
};

export async function parseDataFile(file: File): Promise<ParsedFile> {
  const buf = await file.arrayBuffer();
  const wb = XLSX.read(buf, { type: "array" });
  const ws = wb.Sheets[wb.SheetNames[0]];
  const aoa = XLSX.utils.sheet_to_json<any[]>(ws, { header: 1, blankrows: false });

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

  const numericColumns = columns.filter(
    (c) =>
      c !== "time" &&
      c !== "Trip_Code" &&
      rows.slice(0, 100).some((o) => typeof o[c] === "number" && Number.isFinite(o[c]))
  );

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

export const LINE_COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6"];
