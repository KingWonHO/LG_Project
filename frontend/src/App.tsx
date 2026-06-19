import { BrowserRouter, Routes, Route } from "react-router-dom";
import { RoleProvider } from "@/context";
import Layout from "@/components/Layout";
import UserAnalysis from "@/pages/UserAnalysis";
import Report from "@/pages/Report";
import History from "@/pages/History";
import EngineerAdmin from "@/pages/EngineerAdmin";

export default function App() {
  return (
    <RoleProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<UserAnalysis />} />
            <Route path="report" element={<Report />} />
            <Route path="history" element={<History />} />
            <Route path="engineer" element={<EngineerAdmin />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </RoleProvider>
  );
}
