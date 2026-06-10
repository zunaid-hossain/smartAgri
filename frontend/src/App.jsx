import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Analytics from "./pages/Analytics.jsx";
import AiAssistant from "./pages/AiAssistant.jsx";
import SystemStatus from "./pages/SystemStatus.jsx";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/ai" element={<AiAssistant />} />
        <Route path="/status" element={<SystemStatus />} />
      </Route>
    </Routes>
  );
}
