"use client";

import { useEffect, useState, useCallback } from "react";

interface Trade {
  id: number;
  question: string;
  category: string;
  predicted_outcome: string;
  market_price_at_entry: number;
  our_predicted_probability: number;
  edge: number;
  stake: number;
  potential_payout: number;
  research_summary: string;
  research_sources: string[];
  status: string;
  actual_outcome: string | null;
  pnl: number;
  created_at: string;
  resolved_at: string | null;
  event_end_date: string;
}

export default function TradesPage() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [filter, setFilter] = useState<string>("all");
  const [loading, setLoading] = useState(true);
  const [resolving, setResolving] = useState(false);
  const [expanded, setExpanded] = useState<number | null>(null);

  const fetchTrades = useCallback(async () => {
    try {
      const url =
        filter === "all" ? "/api/trades" : `/api/trades?status=${filter}`;
      const res = await fetch(url);
      setTrades(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchTrades();
  }, [fetchTrades]);

  async function handleResolve(tradeId: number, outcome: string) {
    await fetch(`/api/trades/${tradeId}/resolve?outcome=${outcome}`, {
      method: "POST",
    });
    fetchTrades();
  }

  async function checkResolutions() {
    setResolving(true);
    try {
      await fetch("/api/resolve-all", { method: "POST" });
      fetchTrades();
    } finally {
      setResolving(false);
    }
  }

  const statusColors: Record<string, string> = {
    open: "#ffc048",
    won: "#00d4aa",
    lost: "#ff4757",
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">All Trades</h1>
        <button
          onClick={checkResolutions}
          disabled={resolving}
          className="px-4 py-2 bg-[#1a1a2e] border border-[#2a2a3e] text-white rounded-lg hover:bg-[#2a2a3e] transition text-sm disabled:opacity-50"
        >
          {resolving ? "Checking..." : "Check Resolutions"}
        </button>
      </div>

      <div className="flex gap-2">
        {["all", "open", "won", "lost"].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded-lg text-sm transition ${
              filter === f
                ? "bg-[#5b7fff] text-white"
                : "bg-[#1a1a2e] text-[#8888a0] hover:text-white"
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-12 text-[#8888a0]">Loading...</div>
      ) : trades.length === 0 ? (
        <div className="text-center py-12 text-[#8888a0]">
          No trades found.
        </div>
      ) : (
        <div className="space-y-3">
          {trades.map((trade) => (
            <div
              key={trade.id}
              className="bg-[#1a1a2e] border border-[#2a2a3e] rounded-xl overflow-hidden"
            >
              <div
                className="p-4 cursor-pointer hover:bg-[#1e1e34] transition"
                onClick={() =>
                  setExpanded(expanded === trade.id ? null : trade.id)
                }
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className="inline-block px-2 py-0.5 rounded text-xs font-mono"
                        style={{
                          background: `${statusColors[trade.status]}20`,
                          color: statusColors[trade.status],
                        }}
                      >
                        {trade.status.toUpperCase()}
                      </span>
                      <span className="text-xs text-[#8888a0] font-mono">
                        [{trade.category}]
                      </span>
                      <span className="text-xs text-[#8888a0]">
                        {new Date(trade.created_at).toLocaleDateString()}
                      </span>
                    </div>
                    <div className="text-sm font-medium">{trade.question}</div>
                    <div className="flex flex-wrap gap-4 mt-2 text-xs text-[#8888a0]">
                      <span>
                        Predicted:{" "}
                        <strong className="text-white">
                          {trade.predicted_outcome}
                        </strong>
                      </span>
                      <span>
                        Confidence:{" "}
                        {(trade.our_predicted_probability * 100).toFixed(0)}%
                      </span>
                      <span>
                        Market:{" "}
                        {(trade.market_price_at_entry * 100).toFixed(0)}%
                      </span>
                      <span>Edge: {(trade.edge * 100).toFixed(1)}%</span>
                      <span>Stake: ${trade.stake.toFixed(2)}</span>
                      <span>
                        Payout: ${trade.potential_payout.toFixed(2)}
                      </span>
                      {trade.status !== "open" && (
                        <span
                          style={{
                            color:
                              trade.pnl >= 0 ? "#00d4aa" : "#ff4757",
                          }}
                        >
                          PnL: {trade.pnl >= 0 ? "+" : ""}$
                          {trade.pnl.toFixed(2)}
                        </span>
                      )}
                    </div>
                  </div>
                  {trade.status === "open" && (
                    <div className="flex gap-2 shrink-0">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleResolve(trade.id, "YES");
                        }}
                        className="px-3 py-1 text-xs rounded bg-[#00d4aa20] text-[#00d4aa] hover:bg-[#00d4aa40] transition"
                      >
                        Resolve YES
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleResolve(trade.id, "NO");
                        }}
                        className="px-3 py-1 text-xs rounded bg-[#ff475720] text-[#ff4757] hover:bg-[#ff475740] transition"
                      >
                        Resolve NO
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {expanded === trade.id && (
                <div className="border-t border-[#2a2a3e] p-4 bg-[#12121a]">
                  <h3 className="text-sm font-semibold mb-2">
                    Research Summary
                  </h3>
                  <p className="text-sm text-[#8888a0] mb-3">
                    {trade.research_summary || "No research data available."}
                  </p>
                  {trade.research_sources &&
                    trade.research_sources.length > 0 && (
                      <div>
                        <h4 className="text-xs font-semibold text-[#8888a0] mb-1">
                          Sources:
                        </h4>
                        <ul className="text-xs text-[#5b7fff] space-y-1">
                          {trade.research_sources.map(
                            (src: string, i: number) => (
                              <li key={i} className="truncate">
                                {src}
                              </li>
                            )
                          )}
                        </ul>
                      </div>
                    )}
                  {trade.actual_outcome && (
                    <div className="mt-3 p-3 rounded-lg bg-[#1a1a2e]">
                      <div className="text-xs text-[#8888a0] mb-1">
                        Resolution
                      </div>
                      <div className="text-sm">
                        Actual outcome:{" "}
                        <strong>{trade.actual_outcome}</strong>
                        {" | "}
                        Prediction was{" "}
                        <strong
                          style={{
                            color:
                              trade.status === "won"
                                ? "#00d4aa"
                                : "#ff4757",
                          }}
                        >
                          {trade.status === "won" ? "CORRECT" : "INCORRECT"}
                        </strong>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
