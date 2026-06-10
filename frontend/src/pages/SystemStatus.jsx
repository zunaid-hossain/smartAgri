import { Activity, Clock, Router, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import StatusCard from "../components/StatusCard.jsx";
import { getSystemStatus } from "../services/api.js";
import { formatTime } from "../lib/format.js";

export default function SystemStatus() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const result = await getSystemStatus();
        if (active) {
          setStatus(result);
          setError("");
        }
      } catch (err) {
        if (active) setError("Backend is unreachable");
      }
    };
    load();
    const timer = setInterval(load, 30000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-field">Device health</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-950">System Status</h1>
      </div>
      {error && <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <div className="grid gap-4 md:grid-cols-3">
        <StatusCard title="Sensor Health" value={status?.sensor_health || "Unknown"} detail="Based on latest backend reading" icon={ShieldCheck} tone="field" />
        <StatusCard title="Last Update Time" value={formatTime(status?.last_update_time)} detail="Expected interval: 30 seconds" icon={Clock} tone="warning" />
        <StatusCard title="WiFi Status" value={status?.wifi_status || "Unknown"} detail="ESP32 reports by reaching API" icon={Router} tone="water" />
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
        <div className="flex items-center gap-3">
          <div className="rounded-md bg-field p-3 text-white">
            <Activity size={20} />
          </div>
          <h2 className="text-lg font-semibold text-slate-950">Signal Map</h2>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2">
          <div className="rounded-md bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-900">Real sensor values</p>
            <p className="mt-2 text-sm text-slate-600">{status?.real_values?.join(", ") || "temperature, humidity, soil_moisture, pump_status"}</p>
          </div>
          <div className="rounded-md bg-slate-50 p-4">
            <p className="text-sm font-semibold text-slate-900">Simulated values</p>
            <p className="mt-2 text-sm text-slate-600">{status?.simulated_values?.join(", ") || "nitrogen, phosphorus, potassium"}</p>
          </div>
        </div>
      </section>
    </div>
  );
}
