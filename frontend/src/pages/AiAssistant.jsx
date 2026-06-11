import { Activity, Bot, Clock, RefreshCcw, Send } from "lucide-react";
import { useEffect, useState } from "react";
import { getLatestData, getRecommendation, getRecommendationHistory, getSensorStreamUrl, sendAiChatMessage } from "../services/api.js";
import { formatNumber, formatTime } from "../lib/format.js";

export default function AiAssistant() {
  const [recommendation, setRecommendation] = useState(null);
  const [history, setHistory] = useState([]);
  const [sensorData, setSensorData] = useState(null);
  const [chatMessages, setChatMessages] = useState([
    {
      role: "assistant",
      text: "আমি আপনার SmartAgri সহকারী। সর্বশেষ সেন্সর ডেটা দেখে বাংলায় পরামর্শ দেব।",
    },
  ]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [error, setError] = useState("");
  const [streamStatus, setStreamStatus] = useState("connecting");

  const loadHistory = async () => {
    try {
      const records = await getRecommendationHistory(12);
      setHistory(records);
    } catch (err) {
      setHistory([]);
    }
  };

  const loadSensorData = async () => {
    try {
      const latest = await getLatestData();
      setSensorData(latest);
      setStreamStatus((current) => (current === "live" ? current : "polling fallback"));
    } catch (err) {
      setStreamStatus("waiting for data");
    }
  };

  const load = async () => {
    setLoading(true);
    try {
      const result = await getRecommendation();
      setRecommendation(result);
      await loadHistory();
      setError("");
    } catch (err) {
      setError("AI recommendation will appear after the first sensor reading");
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async (event) => {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed || chatLoading) return;

    setMessage("");
    setChatMessages((current) => [...current, { role: "user", text: trimmed }]);
    setChatLoading(true);
    try {
      const result = await sendAiChatMessage(trimmed);
      setChatMessages((current) => [...current, { role: "assistant", text: result.reply }]);
      setError("");
    } catch (err) {
      setChatMessages((current) => [
        ...current,
        { role: "assistant", text: "দুঃখিত, এখন AI উত্তর পাওয়া যাচ্ছে না। সেন্সর ডেটা ও ব্যাকএন্ড সংযোগ পরীক্ষা করুন।" },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  useEffect(() => {
    load();
    loadSensorData();
    const historyTimer = setInterval(loadHistory, 30000);
    const sensorTimer = setInterval(loadSensorData, 30000);
    const stream = new EventSource(getSensorStreamUrl());

    stream.addEventListener("open", () => {
      setStreamStatus("live");
    });

    stream.addEventListener("sensor-data", (event) => {
      setSensorData(JSON.parse(event.data));
      setStreamStatus("live");
    });

    stream.addEventListener("error", () => {
      setStreamStatus("polling fallback");
    });

    return () => {
      clearInterval(historyTimer);
      clearInterval(sensorTimer);
      stream.close();
    };
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-field">Gemini assistant</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-950">Bangla AI Crop Chat</h1>
        </div>
        <button
          type="button"
          onClick={load}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-md bg-field px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
        >
          <RefreshCcw size={16} />
          Refresh
        </button>
      </div>

      {error && <div className="rounded-md border border-warning/40 bg-amber-50 px-4 py-3 text-sm text-slate-700">{error}</div>}

      <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-panel">
        <div className="flex items-center gap-3">
          <div className="rounded-md bg-field p-3 text-white">
            <Activity size={22} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-950">Realtime sensor context</h2>
            <p className="text-sm text-slate-500">{streamStatus} · {formatTime(sensorData?.created_at)}</p>
          </div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-md bg-slate-50 p-3">
            <p className="text-xs font-semibold uppercase text-slate-500">DHT11 Temperature</p>
            <p className="mt-1 text-lg font-bold text-slate-950">{formatNumber(sensorData?.temperature, " °C")}</p>
          </div>
          <div className="rounded-md bg-slate-50 p-3">
            <p className="text-xs font-semibold uppercase text-slate-500">DHT11 Humidity</p>
            <p className="mt-1 text-lg font-bold text-slate-950">{formatNumber(sensorData?.humidity, "%")}</p>
          </div>
          <div className="rounded-md bg-slate-50 p-3">
            <p className="text-xs font-semibold uppercase text-slate-500">Soil Moisture</p>
            <p className="mt-1 text-lg font-bold text-slate-950">{formatNumber(sensorData?.soil_moisture, "%")}</p>
          </div>
          <div className="rounded-md bg-slate-50 p-3">
            <p className="text-xs font-semibold uppercase text-slate-500">Pump</p>
            <p className="mt-1 text-lg font-bold text-slate-950">{sensorData?.pump_status ? "ON" : sensorData ? "OFF" : "No data"}</p>
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-panel">
        <div className="flex items-center gap-3">
          <div className="rounded-md bg-field p-3 text-white">
            <Bot size={22} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-950">AI chatbox</h2>
            <p className="text-sm text-slate-500">Bangla answers from latest field data</p>
          </div>
        </div>

        <div className="mt-5 max-h-[28rem] space-y-3 overflow-y-auto rounded-md bg-slate-50 p-4">
          {chatMessages.map((item, index) => (
            <div key={`${item.role}-${index}`} className={`flex ${item.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-md px-4 py-3 leading-7 ${item.role === "user" ? "bg-field text-white" : "bg-white text-slate-800"}`}>
                <p className="whitespace-pre-line">{item.text}</p>
              </div>
            </div>
          ))}
          {chatLoading && (
            <div className="flex justify-start">
              <div className="rounded-md bg-white px-4 py-3 text-slate-600">উত্তর তৈরি হচ্ছে...</div>
            </div>
          )}
        </div>

        <form onSubmit={sendMessage} className="mt-4 flex gap-3">
          <input
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="বাংলায় প্রশ্ন লিখুন..."
            className="min-w-0 flex-1 rounded-md border border-slate-300 px-4 py-2 text-sm outline-none focus:border-field"
          />
          <button
            type="submit"
            disabled={chatLoading || !message.trim()}
            className="inline-flex items-center justify-center rounded-md bg-field px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
            aria-label="Send message"
          >
            <Send size={18} />
          </button>
        </form>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-panel">
        <div className="flex items-center gap-3">
          <div className="rounded-md bg-field p-3 text-white">
            <Bot size={22} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-950">Latest recommendation</h2>
            <p className="text-sm text-slate-500">
              Source: {recommendation?.source || "not generated"} · {formatTime(recommendation?.saved?.created_at)}
            </p>
          </div>
        </div>
        <div className="mt-6 whitespace-pre-line rounded-md bg-slate-50 p-4 leading-7 text-slate-800">
          {loading ? "Generating recommendation..." : recommendation?.recommendation || "No recommendation yet."}
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-panel">
        <div className="flex items-center gap-3">
          <div className="rounded-md bg-water p-3 text-white">
            <Clock size={22} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-950">Previous recommendations</h2>
            <p className="text-sm text-slate-500">Stored from earlier AI runs</p>
          </div>
        </div>

        <div className="mt-5 space-y-3">
          {history.length ? (
            history.map((item) => (
              <article key={item.id} className="rounded-md bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase text-slate-500">{formatTime(item.created_at)}</p>
                <p className="mt-2 line-clamp-4 whitespace-pre-line leading-7 text-slate-800">{item.recommendation}</p>
              </article>
            ))
          ) : (
            <p className="rounded-md bg-slate-50 p-4 text-sm text-slate-600">No previous recommendations yet.</p>
          )}
        </div>
      </section>
    </div>
  );
}
