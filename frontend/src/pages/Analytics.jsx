import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import ChartPanel from "../components/ChartPanel.jsx";
import { getHistory } from "../services/api.js";

const formatChartTime = (value) => new Date(value).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

export default function Analytics() {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const records = await getHistory(120);
        if (active) {
          setHistory(records);
          setError("");
        }
      } catch (err) {
        if (active) setError("No history available yet");
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
        <p className="text-sm font-semibold uppercase tracking-wide text-field">Field analytics</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-950">Sensor History</h1>
      </div>
      {error && <div className="rounded-md border border-warning/40 bg-amber-50 px-4 py-3 text-sm text-slate-700">{error}</div>}

      <div className="grid gap-5 xl:grid-cols-2">
        <ChartPanel title="Soil Moisture History">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="created_at" tickFormatter={formatChartTime} minTickGap={24} />
              <YAxis domain={[0, 100]} />
              <Tooltip labelFormatter={(value) => new Date(value).toLocaleString()} />
              <Area type="monotone" dataKey="soil_moisture" stroke="#256d3b" fill="#cfe8d5" name="Soil Moisture %" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartPanel>

        <ChartPanel title="Temperature History">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="created_at" tickFormatter={formatChartTime} minTickGap={24} />
              <YAxis />
              <Tooltip labelFormatter={(value) => new Date(value).toLocaleString()} />
              <Line type="monotone" dataKey="temperature" stroke="#c47c1d" strokeWidth={2} dot={false} name="Temperature °C" />
            </LineChart>
          </ResponsiveContainer>
        </ChartPanel>

        <ChartPanel title="Humidity History">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="created_at" tickFormatter={formatChartTime} minTickGap={24} />
              <YAxis domain={[0, 100]} />
              <Tooltip labelFormatter={(value) => new Date(value).toLocaleString()} />
              <Area type="monotone" dataKey="humidity" stroke="#1b7aa7" fill="#d5edf7" name="Humidity %" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartPanel>

        <ChartPanel title="NPK History">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="created_at" tickFormatter={formatChartTime} minTickGap={24} />
              <YAxis />
              <Tooltip labelFormatter={(value) => `${new Date(value).toLocaleString()} · simulated NPK`} />
              <Legend />
              <Line type="monotone" dataKey="nitrogen" stroke="#256d3b" strokeWidth={2} dot={false} name="Nitrogen simulated" />
              <Line type="monotone" dataKey="phosphorus" stroke="#7a5c36" strokeWidth={2} dot={false} name="Phosphorus simulated" />
              <Line type="monotone" dataKey="potassium" stroke="#c47c1d" strokeWidth={2} dot={false} name="Potassium simulated" />
            </LineChart>
          </ResponsiveContainer>
        </ChartPanel>
      </div>
    </div>
  );
}
