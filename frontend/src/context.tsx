import { createContext, useContext, useState, type ReactNode } from "react";

export type Role = "user" | "engineer";

const RoleContext = createContext<{ role: Role; setRole: (r: Role) => void }>({
  role: "user",
  setRole: () => {},
});

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRole] = useState<Role>("user");
  return <RoleContext.Provider value={{ role, setRole }}>{children}</RoleContext.Provider>;
}

export const useRole = () => useContext(RoleContext);

export const MOCK_ACCESS_CODE = "1234";
