import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api, type HistoryItem, type AnalyzeResponse } from "@/lib/api";

export type Role = "user" | "engineer";

type Ctx = {
  role: Role;
  setRole: (r: Role) => void;
  history: HistoryItem[];
  refreshHistory: () => Promise<void>;
  selected: HistoryItem | null;
  setSelected: (h: HistoryItem | null) => void;
  lastResult: AnalyzeResponse | null;
  setLastResult: (r: AnalyzeResponse | null) => void;
};

const AppContext = createContext<Ctx>({
  role: "user",
  setRole: () => {},
  history: [],
  refreshHistory: async () => {},
  selected: null,
  setSelected: () => {},
  lastResult: null,
  setLastResult: () => {},
});

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role>("user");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [selected, setSelected] = useState<HistoryItem | null>(null);
  const [lastResult, setLastResult] = useState<AnalyzeResponse | null>(null);

  const refreshHistory = async () => {
    try {
      setHistory(await api.history());
    } catch {
      // 백엔드 미기동 시 빈 목록 유지
    }
  };

  useEffect(() => {
    refreshHistory();
  }, []);

  return (
    <AppContext.Provider
      value={{ role, setRole, history, refreshHistory, selected, setSelected, lastResult, setLastResult }}
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
