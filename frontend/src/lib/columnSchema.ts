// trip_case.json 의 schema_reference 를 프론트에 번들한 컬럼 매핑.
// 정책(column_mapping_policy): CSV 원본 컬럼명은 신뢰하지 않고 column_index 로 매핑한다.
// 평압 = NODPS, 차압 = DPS. 인덱스 9·16·17 만 모드에 따라 이름이 달라진다.

export type PressureMode = "평압" | "차압";

// 공통 컬럼 (모드 무관)
const COMMON: Record<number, string> = {
  0: "Time",
  1: "Imag",
  2: "unused_1",
  3: "DC_link",
  4: "Ref_Hz",
  5: "Real_Hz",
  6: "unused_2",
  7: "Power",
  8: "IPM",
  10: "Ramp_Hz",
  11: "LeadA",
  12: "LeadA_FW",
  13: "LeadA_Add",
  14: "LeadA_Total",
  15: "MtoC",
  18: "R_temp",
  19: "Avg_Torque",
  20: "Trip",
};

// 평압(NODPS) 전용
const NODPS: Record<number, string> = { 9: "Wait_Time", 16: "unused_3", 17: "unused_4" };
// 차압(DPS) 전용
const DPS: Record<number, string> = { 9: "Trial_Count", 16: "1st_Freq", 17: "2nd_Freq" };

export const TIME_INDEX = 0;
export const TRIP_INDEX = 20;

/** 컬럼 인덱스 → 평압/차압별 canonical_name. 스키마에 없으면 null. */
export function canonicalName(index: number, mode: PressureMode): string | null {
  if (index in COMMON) return COMMON[index];
  const m = mode === "차압" ? DPS : NODPS;
  return m[index] ?? null;
}

/** 그래프에 그릴 수 있는 컬럼인지: 스키마 정의 + Time/Trip/unused 제외 (모드별로 16·17 달라짐). */
export function isPlottable(index: number, mode: PressureMode): boolean {
  if (index === TIME_INDEX || index === TRIP_INDEX) return false;
  const n = canonicalName(index, mode);
  return !!n && !n.startsWith("unused");
}

// ---------------------------------------------------------------------------
// 정상범위 / 노이즈 (엔지니어 스펙: 연번 = column_index 기준)
//   정상범위를 벗어난 값은 노이즈로 보고 전처리(그래프에서 제거)한다.
//   [min, max] (null = 제한 없음). 음수(이상치)는 min=0 으로 처리. "전체"는 [null, null].
// ---------------------------------------------------------------------------
type Bounds = [number | null, number | null];

const NOISE_COMMON: Record<number, Bounds> = {
  1: [null, null],   // Imag (전체)
  2: [null, null],   // (전체)
  3: [100, 400],     // DC_link  (100<x<400)
  4: [0, 100],       // Ref_Hz
  5: [0, 100],       // Real_Hz
  6: [null, null],   // (전체)
  7: [0, 600],       // Power
  8: [0, 300],       // IPM
  10: [0, 100],      // Ramp_Hz
  11: [0, 3000],     // LeadA
  12: [0, 3000],     // LeadA_FW
  13: [0, 3000],     // LeadA_Add
  14: [0, 3000],     // LeadA_Total
  15: [0, 255],      // MtoC
  18: [0, 300],      // R_temp
  19: [0, 2000],     // Avg_Torque
  20: [0, 20],       // Trip
};
// 모드에 따라 다른 컬럼(9·16·17)
const NOISE_NODPS: Record<number, Bounds> = { 9: [0, 1000], 16: [0, 255], 17: [0, 255] };
const NOISE_DPS: Record<number, Bounds> = { 9: [0, 255], 16: [0, 100], 17: [0, 100] };

/** 컬럼 인덱스+모드의 정상범위 [min, max]. 정의 없으면 null. */
export function noiseBounds(index: number, mode: PressureMode): Bounds | null {
  if (index === 9 || index === 16 || index === 17) {
    return (mode === "차압" ? NOISE_DPS : NOISE_NODPS)[index] ?? null;
  }
  return NOISE_COMMON[index] ?? null;
}

/** 값이 정상범위를 벗어난 노이즈인지. 범위 미정의 컬럼은 항상 false. */
export function isNoise(index: number, mode: PressureMode, value: number): boolean {
  const b = noiseBounds(index, mode);
  if (!b) return false;
  const [min, max] = b;
  if (!Number.isFinite(value)) return false;
  if (min !== null && value < min) return true;
  if (max !== null && value > max) return true;
  return false;
}
