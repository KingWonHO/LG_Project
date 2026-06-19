export type Point = { time: number; 컴프전류: number; 전압: number; RT: number };

export const TRIP_RANGE: [number, number] = [150, 172];

export function mockTimeseries(n = 300): Point[] {
  const out: Point[] = [];
  for (let t = 0; t < n; t++) {
    let comp = 50 + 5 * Math.sin(t / 15) + (Math.random() - 0.5);
    if (t >= TRIP_RANGE[0] && t < TRIP_RANGE[1]) comp += 18;
    out.push({
      time: t,
      컴프전류: +comp.toFixed(2),
      전압: +(220 + 3 * Math.sin(t / 40) + (Math.random() - 0.5)).toFixed(2),
      RT: +(25 + 2 * Math.sin(t / 50)).toFixed(2),
    });
  }
  return out;
}

export const mockResult = [
  { 항목: "Trip 발생", 결과: "3회 (구간 150~172)" },
  { 항목: "baseline 이탈", 결과: "CoolingPower 초과" },
  { 항목: "데이터 품질", 결과: "이상치 2건" },
  { 항목: "최종 판정", 결과: "관리필요" },
];

export const mockHistory = [
  { 일시: "2026-06-18 09:12", 파일명: "comp_A_0618.csv", 행수: 1820, 판정: "관리필요" },
  { 일시: "2026-06-17 16:40", 파일명: "comp_B_0617.xlsx", 행수: 2400, 판정: "PASS" },
  { 일시: "2026-06-17 10:05", 파일명: "comp_A_0617.csv", 행수: 1755, 판정: "FAIL" },
];

export const mockTripCodes = [
  { code: 101, 의미: "과전류", 원인: "컴프 과부하", 조치: "전류 점검" },
  { code: 205, 의미: "고온", 원인: "냉각 부족", 조치: "냉매 점검" },
  { code: 310, 의미: "통신 오류", 원인: "센서 단선", 조치: "배선 점검" },
];
