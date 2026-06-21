import { createContext, useContext, useState, type ReactNode } from "react";

export type Role = "user" | "engineer";

export type AnalysisRecord = {
  id: string;
  filename: string;
  time: string;
  verdict: string;           // PASS | 관리필요 | FAIL
  trip: string;              // 요약용 (예: "Trip 3회")
  narrative: string;         // 챗 스타일 본문
  result: { 항목: string; 결과: string }[];
};

type Ctx = {
  role: Role;
  setRole: (r: Role) => void;
  history: AnalysisRecord[];
  addRecord: (r: AnalysisRecord) => void;
  selectedId: string | null;
  setSelectedId: (id: string | null) => void;
};

const seed: AnalysisRecord[] = [
  {
    id: "seed-1",
    filename: "comp_A_0617.csv",
    time: "2026-06-17 10:05",
    verdict: "FAIL",
    trip: "Trip 7회",
    narrative:
      "comp_A_0617.csv 분석 결과 Trip이 7회 발생했고 컴프 전류가 반복적으로 임계치를 초과했습니다. 종합적으로 FAIL로 판정합니다.",
    result: [
      { 항목: "Trip 발생", 결과: "7회" },
      { 항목: "baseline 이탈", 결과: "Iqe, CoolingPower" },
      { 항목: "데이터 품질", 결과: "이상치 5건" },
      { 항목: "최종 판정", 결과: "FAIL" },
    ],
  },
  {
    id: "seed-2",
    filename: "comp_B_0617.xlsx",
    time: "2026-06-17 16:40",
    verdict: "PASS",
    trip: "Trip 0회",
    narrative:
      "comp_B_0617.xlsx 분석 결과 Trip이 없고 모든 항목이 정상 baseline 범위 내에 있습니다. PASS로 판정합니다.",
    result: [
      { 항목: "Trip 발생", 결과: "0회" },
      { 항목: "baseline 이탈", 결과: "없음" },
      { 항목: "데이터 품질", 결과: "정상" },
      { 항목: "최종 판정", 결과: "PASS" },
    ],
  },
];

const AppContext = createContext<Ctx>({
  role: "user",
  setRole: () => {},
  history: [],
  addRecord: () => {},
  selectedId: null,
  setSelectedId: () => {},
});

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role>("user");
  const [history, setHistory] = useState<AnalysisRecord[]>(seed);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const addRecord = (r: AnalysisRecord) => setHistory((prev) => [r, ...prev]);
  return (
    <AppContext.Provider value={{ role, setRole, history, addRecord, selectedId, setSelectedId }}>
      {children}
    </AppContext.Provider>
  );
}

export const useRole = () => {
  const { role, setRole } = useContext(AppContext);
  return { role, setRole };
};
export const useApp = () => useContext(AppContext);

export const MOCK_ACCESS_CODE = "1234";
