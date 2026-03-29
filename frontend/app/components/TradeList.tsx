"use client";

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
  status: string;
  actual_outcome: string | null;
  pnl: number;
  created_at: string;
  resolved_at: string | null;
}

const statusColors: Record<string, string> = {
  open: "#ffc048",
  won: "#00d4aa",
  lost: "#ff4757",
};

const categoryEmoji: Record<string, string> = {
  politics: "P",
  sports: "S",
  crypto: "C",
  entertainment: "E",
  finance: "F",
  science: "Sc",
  other: "O",
};

export default function TradeList({
  trades,
  onResolve,
  showDetails = false,
}: {
  trades: Trade[];
  onResolve?: (id: number, outcome: string) => void;
  showDetails?: boolean;
}) {
  if (!trades || trades.length === 0) {
    return (
      <div className="text-[#8888a0] text-center py-8">
        No trades yet. Go to Events to scan and place trades.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {trades.map((trade) => (
        <div
          key={trade.id}
          className="bg-[#1a1a2e] border border-[#2a2a3e] rounded-xl p-4"
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
                  [{categoryEmoji[trade.category] || "O"}]
                </span>
              </div>
              <a
                href={`/trades#${trade.id}`}
                className="text-sm font-medium hover:text-[#5b7fff] transition line-clamp-2"
              >
                {trade.question}
              </a>
              <div className="flex flex-wrap gap-4 mt-2 text-xs text-[#8888a0]">
                <span>
                  Predicted:{" "}
                  <strong className="text-white">
                    {trade.predicted_outcome}
                  </strong>{" "}
                  @ {(trade.our_predicted_probability * 100).toFixed(0)}%
                </span>
                <span>
                  Market: {(trade.market_price_at_entry * 100).toFixed(0)}%
                </span>
                <span>Edge: {(trade.edge * 100).toFixed(1)}%</span>
                <span>Stake: ${trade.stake.toFixed(2)}</span>
                {trade.status !== "open" && (
                  <span
                    style={{
                      color:
                        trade.pnl >= 0 ? "#00d4aa" : "#ff4757",
                    }}
                  >
                    PnL: {trade.pnl >= 0 ? "+" : ""}${trade.pnl.toFixed(2)}
                  </span>
                )}
              </div>
            </div>
            {trade.status === "open" && onResolve && (
              <div className="flex gap-2 shrink-0">
                <button
                  onClick={() => onResolve(trade.id, "YES")}
                  className="px-3 py-1 text-xs rounded bg-[#00d4aa20] text-[#00d4aa] hover:bg-[#00d4aa40] transition"
                >
                  YES
                </button>
                <button
                  onClick={() => onResolve(trade.id, "NO")}
                  className="px-3 py-1 text-xs rounded bg-[#ff475720] text-[#ff4757] hover:bg-[#ff475740] transition"
                >
                  NO
                </button>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
