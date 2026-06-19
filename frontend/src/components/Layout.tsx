import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, FileText, History, Wrench, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useRole, MOCK_ACCESS_CODE } from "@/context";
import { cn } from "@/lib/utils";

const navBase =
  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors";

export default function Layout() {
  const { role, setRole } = useRole();
  const [code, setCode] = useState("");
  const [err, setErr] = useState(false);

  const link = ({ isActive }: { isActive: boolean }) =>
    cn(navBase, isActive ? "bg-secondary text-foreground" : "text-muted-foreground hover:bg-secondary/60");

  return (
    <div className="flex min-h-screen">
      <aside className="w-60 shrink-0 border-r bg-card p-4 flex flex-col gap-1">
        <div className="px-2 py-3">
          <h1 className="text-sm font-medium">LG Comp 확인 에이전트</h1>
          <p className="text-xs text-muted-foreground">분석 자동화</p>
        </div>

        <nav className="flex flex-col gap-1">
          <NavLink to="/" end className={link}><BarChart3 className="h-4 w-4" /> 사용자 분석</NavLink>
          <NavLink to="/report" className={link}><FileText className="h-4 w-4" /> 리포트</NavLink>
          <NavLink to="/history" className={link}><History className="h-4 w-4" /> 분석 이력</NavLink>
          {role === "engineer" && (
            <NavLink to="/engineer" className={link}><Wrench className="h-4 w-4" /> 엔지니어 관리</NavLink>
          )}
        </nav>

        <div className="mt-auto border-t pt-4">
          <p className="px-2 mb-2 text-xs text-muted-foreground">접근 권한</p>
          {role === "engineer" ? (
            <div className="px-2 space-y-2">
              <Badge variant="success">엔지니어 모드</Badge>
              <Button variant="outline" size="sm" className="w-full" onClick={() => setRole("user")}>
                <LogOut className="h-4 w-4" /> 로그아웃
              </Button>
            </div>
          ) : (
            <div className="px-2 space-y-2">
              <Badge variant="secondary">일반 사용자</Badge>
              <Input
                type="password"
                placeholder="엔지니어 접근 코드"
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
              {err && <p className="text-xs text-destructive">코드가 올바르지 않습니다.</p>}
              <Button
                size="sm"
                className="w-full"
                onClick={() => (code === MOCK_ACCESS_CODE ? setRole("engineer") : setErr(true))}
              >
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
