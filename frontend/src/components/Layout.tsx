import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { BarChart3, FileText, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useRole, useApp, MOCK_ACCESS_CODE } from "@/context";
import { cn } from "@/lib/utils";

const navBase = "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors";

function verdictColor(v: string) {
  return v === "PASS" ? "text-emerald-600" : v === "FAIL" ? "text-destructive" : "text-amber-600";
}

export default function Layout() {
  const { role, setRole } = useRole();
  const { history, selected, setSelected } = useApp();
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [err, setErr] = useState(false);

  const link = ({ isActive }: { isActive: boolean }) =>
    cn(navBase, isActive ? "bg-secondary text-foreground" : "text-muted-foreground hover:bg-secondary/60");

  return (
    <div className="flex h-screen">
      <aside className="w-64 shrink-0 border-r bg-card flex flex-col">
        <div className="px-4 pt-4 pb-2">
          <h1 className="text-sm font-medium">LG Comp 확인 에이전트</h1>
          <p className="text-xs text-muted-foreground">분석 자동화</p>
        </div>

        <nav className="flex flex-col gap-1 px-3">
          <NavLink to="/" end className={link}><BarChart3 className="h-4 w-4" /> 사용자 분석</NavLink>
          <NavLink to="/report" className={link}><FileText className="h-4 w-4" /> 리포트</NavLink>
        </nav>

        <div className="mt-3 flex-1 min-h-0 flex flex-col border-t pt-3">
          <p className="px-4 pb-2 text-xs font-medium text-muted-foreground">분석 이력</p>
          <div className="flex-1 overflow-y-auto px-3 space-y-1">
            {history.length === 0 ? (
              <p className="px-1 text-xs text-muted-foreground">분석 기록이 없습니다.</p>
            ) : (
              history.map((h, i) => (
                <button
                  key={i}
                  onClick={() => { setSelected(h); navigate("/history"); }}
                  className={cn(
                    "w-full text-left rounded-md px-3 py-2 transition-colors",
                    selected === h ? "bg-secondary" : "hover:bg-secondary/60"
                  )}
                >
                  <p className="text-xs font-medium truncate">{h.파일명}</p>
                  <p className="text-[11px] text-muted-foreground truncate">
                    <span className={verdictColor(h.판정)}>{h.판정}</span>
                    {h.행수 != null ? ` · ${h.행수.toLocaleString()}행` : ""}
                  </p>
                  <p className="text-[10px] text-muted-foreground/70">{h.일시}</p>
                </button>
              ))
            )}
          </div>
        </div>

        <div className="border-t p-4">
          <p className="mb-2 text-xs text-muted-foreground">접근 권한</p>
          {role === "engineer" ? (
            <div className="space-y-2">
              <Badge variant="success">엔지니어 모드</Badge>
              <Button variant="outline" size="sm" className="w-full" onClick={() => setRole("user")}>
                <LogOut className="h-4 w-4" /> 로그아웃
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              <Badge variant="secondary">일반 사용자</Badge>
              <Input type="password" placeholder="엔지니어 접근 코드"
                     value={code} onChange={(e) => setCode(e.target.value)} />
              {err && <p className="text-xs text-destructive">코드가 올바르지 않습니다.</p>}
              <Button size="sm" className="w-full"
                onClick={() => (code === MOCK_ACCESS_CODE ? setRole("engineer") : setErr(true))}>
                엔지니어 로그인
              </Button>
            </div>
          )}
        </div>
      </aside>

      <main className="flex-1 p-6 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
