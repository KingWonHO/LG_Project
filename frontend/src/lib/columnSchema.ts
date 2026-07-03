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
