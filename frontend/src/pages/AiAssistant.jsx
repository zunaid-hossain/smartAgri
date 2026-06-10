import { Bot, RefreshCcw } from "lucide-react";
import { useEffect, useState } from "react";
import { getRecommendation } from "../services/api.js";
import { formatTime } from "../lib/format.js";

export default function AiAssistant() {
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const result = await getRecommendation();
      setRecommendation(result);
      setError("");
    } catch (err) {
      setError("AI recommendation will appear after the first sensor reading");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const timer = setInterval(load, 30000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-field">Gemini assistant</p>
          <h1 className="mt-2 text-3xl font-bold text-slate-950">Bangla Crop Recommendation</h1>
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
    </div>
  );
}
