import { Droplets, FlaskConical, Gauge, Power, Sprout, Thermometer, Waves } from "lucide-react";
import { useEffect, useState } from "react";
import StatusCard from "../components/StatusCard.jsx";
import { getLatestData, getSensorStreamUrl } from "../services/api.js";
import { formatNumber, formatTime } from "../lib/format.js";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const latest = await getLatestData();
        if (active) {
          setData(latest);
          setError("");
        }
      } catch (err) {
        if (active) setError("Waiting for ESP32 sensor data");
      }
    };
    load();
    const timer = setInterval(load, 30000);
    const stream = new EventSource(getSensorStreamUrl());

    stream.addEventListener("open", () => {
      if (active) setStreamStatus("live");
    });

    stream.addEventListener("sensor-data", (event) => {
      if (!active) return;
      setData(JSON.parse(event.data));
      setError("");
      setStreamStatus("live");
    });

    stream.addEventListener("error", () => {
      if (active) setStreamStatus("polling fallback");
    });

    return () => {
      active = false;
      stream.close();
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-field">Live field dashboard</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-950">AI-Powered Smart Agriculture</h1>
        <p className="mt-2 text-slate-600">Real-time ESP32 sensor telemetry with polling fallback.</p>
      </div>

      {error && <div className="rounded-md border border-warning/40 bg-amber-50 px-4 py-3 text-sm text-slate-700">{error}</div>}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatusCard title="Temperature" value={formatNumber(data?.temperature, " °C")} detail="DHT11 sensor value" icon={Thermometer} tone="warning" />
        <StatusCard title="Humidity" value={formatNumber(data?.humidity, "%")} detail="DHT11 sensor value" icon={Waves} tone="water" />
        <StatusCard title="Soil Moisture" value={formatNumber(data?.soil_moisture, "%")} detail="Real analog sensor value" icon={Droplets} tone="field" />
        <StatusCard title="Pump Status" value={data?.pump_status ? "ON" : data ? "OFF" : "No data"} detail="Relay-controlled water pump" icon={Power} tone={data?.pump_status ? "water" : "earth"} />
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <StatusCard title="Nitrogen" value={formatNumber(data?.nitrogen)} detail="NPK sensor value: 20-80" icon={FlaskConical} tone="field" />
        <StatusCard title="Phosphorus" value={formatNumber(data?.phosphorus)} detail="NPK sensor value: 5-45" icon={Sprout} tone="earth" />
        <StatusCard title="Potassium" value={formatNumber(data?.potassium)} detail="NPK sensor value: 20-100" icon={Gauge} tone="warning" />
      </div>

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <p className="text-sm text-slate-500">Last update</p>
            <p className="mt-1 font-semibold text-slate-900">{formatTime(data?.created_at)}</p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Auto irrigation rule</p>
            <p className="mt-1 font-semibold text-slate-900">Pump ON when soil moisture is below 30%</p>
          </div>
          <div>
            <p className="text-sm text-slate-500">Realtime monitor</p>
            <p className="mt-1 font-semibold text-slate-900">{streamStatus}</p>
          </div>
        </div>
      </section>
    </div>
  );
}
