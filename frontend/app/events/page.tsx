"use client";

import { useEffect, useState } from "react";

interface MarketEvent {
  event_id: string;
  condition_id: string;
  question: string;
  description: string;
  category: string;
  yes_price: number;
  no_price: number;
  volume: number;
  liquidity: number;
  end_date: string;
}

export default function EventsPage() {
  const [events, setEvents] = useState<MarketEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [scanResults, setScanResults] = useState<any>(null);
  const [researchingId, setResearchingId] = useState<string | null>(null);
  const [researchResult, setResearchResult] = useState<any>(null);

  useEffect(() => {
    fetchEvents();
  }, []);

  async function fetchEvents() {
    setLoading(true);
    try {
      const res = await fetch("/api/events");
      const data = await res.json();
      setEvents(data);
    } catch (e) {
      console.error("Failed to fetch events:", e);
    } finally {
      setLoading(false);
    }
  }

  async function autoScan() {
    setScanning(true);
    setScanResults(null);
    try {
      const res = await fetch("/api/auto-scan", { method: "POST" });
      const data = await res.json();
      setScanResults(data);
    } catch (e) {
      console.error("Auto scan failed:", e);
    } finally {
      setScanning(false);
    }
  }

  async function researchEvent(event: MarketEvent) {
    setResearchingId(event.event_id);
    setResearchResult(null);
    try {
      const params = new URLSearchParams({
        event_id: event.event_id,
        condition_id: event.condition_id || "",
        question: event.question,
        category: event.category,
        yes_price: event.yes_price.toString(),
        end_date: event.end_date || "",
      });
      const res = await fetch(`/api/research?${params}`, { method: "POST" });
      const data = await res.json();
      setResearchResult(data);
    } catch (e) {
      console.error("Research failed:", e);
    } finally {
      setResearchingId(null);
    }
  }

  function formatVolume(v: number): string {
    if (v >= 1_000_000) return `$${(v / 1_000_000).toFixed(1)}M`;
    if (v >= 1_000) return `$${(v / 1_000).toFixed(0)}K`;
    return `$${v.toFixed(0)}`;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Short-Term Events</h1>
        <div className="flex gap-3">
          <button
            onClick={fetchEvents}
            className="px-4 py-2 bg-[#1a1a2e] border border-[#2a2a3e] text-white rounded-lg hover:bg-[#2a2a3e] transition text-sm"
          >
            Refresh
          </button>
          <button
            onClick={autoScan}
            disabled={scanning}
            className="px-4 py-2 bg-[#5b7fff] text-white rounded-lg hover:bg-[#4a6eee] transition text-sm font-medium disabled:opacity-50"
          >
            {scanning ? "Scanning..." : "Auto-Scan & Trade"}
          </button>
        </div>
      </div>

      {scanResults && (
        <div className="bg-[#1a1a2e] border border-[#2a2a3e] rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-3">
            Scan Results ({scanResults.scanned} events analyzed)
          </h2>
          <div className="space-y-3">
            {scanResults.results?.map((r: any, i: number) => (
              <div
                key={i}
                className="border border-[#2a2a3e] rounded-lg p-3"
              >
                <div className="text-sm font-medium mb-1">{r.question}</div>
                {r.error ? (
                  <div className="text-xs text-[#ff4757]">Error: {r.error}</div>
                ) : (
                  <div className="text-xs text-[#8888a0]">
                    Prediction: {r.research?.predicted_outcome} @{" "}
                    {((r.research?.confidence || 0) * 100).toFixed(0)}% confidence
                    {r.trade_placed ? (
                      <span className="text-[#00d4aa] ml-2">
                        Trade placed: ${r.trade?.stake.toFixed(2)}
                      </span>
                    ) : (
                      <span className="text-[#ffc048] ml-2">
                        No trade (insufficient edge)
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {researchResult && (
        <div className="bg-[#1a1a2e] border border-[#5b7fff40] rounded-xl p-6">
          <h2 className="text-lg font-semibold mb-3">Research Result</h2>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-[#8888a0]">Prediction: </span>
              <strong
                style={{
                  color:
                    researchResult.research?.predicted_outcome === "YES"
                      ? "#00d4aa"
                      : "#ff4757",
                }}
              >
                {researchResult.research?.predicted_outcome}
              </strong>
              <span className="text-[#8888a0] ml-2">
                ({((researchResult.research?.confidence || 0) * 100).toFixed(0)}%
                confidence)
              </span>
            </div>
            <div className="text-[#8888a0]">
              {researchResult.research?.summary}
            </div>
            {researchResult.research?.key_factors?.length > 0 && (
              <div>
                <div className="text-xs text-[#8888a0] mt-2 mb-1">
                  Key Factors:
                </div>
                <ul className="text-xs text-[#8888a0] list-disc pl-4">
                  {researchResult.research.key_factors.map(
                    (f: string, i: number) => (
                      <li key={i}>{f}</li>
                    )
                  )}
                </ul>
              </div>
            )}
            {researchResult.trade_placed ? (
              <div className="text-[#00d4aa] text-xs mt-2">
                Trade placed: ${researchResult.trade?.stake.toFixed(2)} on{" "}
                {researchResult.trade?.predicted_outcome}
              </div>
            ) : (
              <div className="text-[#ffc048] text-xs mt-2">
                {researchResult.reason}
              </div>
            )}
          </div>
          <button
            onClick={() => setResearchResult(null)}
            className="mt-3 text-xs text-[#8888a0] hover:text-white transition"
          >
            Dismiss
          </button>
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-[#8888a0]">
          Loading events from Polymarket...
        </div>
      ) : events.length === 0 ? (
        <div className="text-center py-12 text-[#8888a0]">
          No short-term events found. Try refreshing.
        </div>
      ) : (
        <div className="grid gap-4">
          {events.map((event) => (
            <div
              key={`${event.event_id}-${event.condition_id}`}
              className="bg-[#1a1a2e] border border-[#2a2a3e] rounded-xl p-4 hover:border-[#5b7fff40] transition"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs px-2 py-0.5 bg-[#5b7fff20] text-[#5b7fff] rounded font-mono">
                      {event.category}
                    </span>
                    {event.end_date && (
                      <span className="text-xs text-[#8888a0]">
                        Ends:{" "}
                        {new Date(event.end_date).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    )}
                  </div>
                  <div className="text-sm font-medium mb-2">
                    {event.question}
                  </div>
                  <div className="flex gap-4 text-xs text-[#8888a0]">
                    <span>
                      YES:{" "}
                      <strong className="text-[#00d4aa]">
                        {(event.yes_price * 100).toFixed(0)}c
                      </strong>
                    </span>
                    <span>
                      NO:{" "}
                      <strong className="text-[#ff4757]">
                        {(event.no_price * 100).toFixed(0)}c
                      </strong>
                    </span>
                    <span>Vol: {formatVolume(event.volume)}</span>
                  </div>
                </div>
                <button
                  onClick={() => researchEvent(event)}
                  disabled={researchingId === event.event_id}
                  className="px-4 py-2 bg-[#5b7fff20] text-[#5b7fff] rounded-lg hover:bg-[#5b7fff40] transition text-sm shrink-0 disabled:opacity-50"
                >
                  {researchingId === event.event_id
                    ? "Researching..."
                    : "Research & Trade"}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
