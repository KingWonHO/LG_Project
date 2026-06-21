import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type HistoryItem, type AnalyzeResponse, type ReportData } from "@/lib/api";
import type { ParsedFile } from "@/lib/parseFile";

export type Role = "user" | "engineer";

export type UAState = {
  file: File | null;
  parsed: ParsedFile | null;
  cols: string[];
  result: AnalyzeResponse | null;
};

type Ctx = {
  role: Role;
  setRole: (r: Role) => void;
  history: HistoryItem[];
  refreshHistory: () => Promise<void>;
  selected: HistoryItem | null;
  setSelected: (h: HistoryItem | null) => void;
  lastResult: AnalyzeResponse | null;
  setLastResult: (r: AnalyzeResponse | null) => void;
  backendUp: boolean | null;
  ua: UAState;
  setUa: (patch: Partial<UAState>) => void;
  reportData: ReportData | null;
  setReportData: (r: ReportData | null) => void;
};

const EMPTY_UA: UAState = { file: null, parsed: null, cols: [], result: null };

const AppContext = createContext<Ctx>({
  role: "user",
  setRole: () => {},
  history: [],
  refreshHistory: async () => {},
  selected: null,
  setSelected: () => {},
  lastResult: null,
  setLastResult: () => {},
  backendUp: null,
  ua: EMPTY_UA,
  setUa: () => {},
  reportData: null,
  setReportData: () => {},
});

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role>("user");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selected, setSelected] = useState<HistoryItem | null>(null);
  const [lastResult, setLastResult] = useState<AnalyzeResponse | null>(null);
  const [backendUp, setBackendUp] = useState<boolean | null>(null);
  const [ua, setUaState] = useState<UAState>(EMPTY_UA);
  const [reportData, setReportData] = useState<ReportData | null>(null);
  const setUa = (patch: Partial<UAState>) => setUaState((prev) => ({ ...prev, ...patch }));

  const refreshHistory = async () => {
    try { setHistory(await api.history()); } catch { /* 무시 */ }
  };

  useEffect(() => {
    let alive = true;
    const ping = async () => {
      try { await api.health(); if (alive) setBackendUp(true); }
      catch { if (alive) setBackendUp(false); }
    };
    ping();
    refreshHistory();
    const id = setInterval(ping, 10000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  return (
    <AppContext.Provider
      value={{ role, setRole, history, refreshHistory, selected, setSelected,
               lastResult, setLastResult, backendUp, ua, setUa, reportData, setReportData }}
    >
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
