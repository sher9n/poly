"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface HistoryPoint {
  bankroll: number;
  timestamp: string;
  event: string;
}

export default function BankrollChart({ data }: { data: HistoryPoint[] }) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-[#1a1a2e] border border-[#2a2a3e] rounded-xl p-6">
        <h2 className="text-lg font-semibold mb-4">Bankroll Over Time</h2>
        <div className="text-[#8888a0] text-center py-12">
          No history yet. Place some trades to see your bankroll chart.
        </div>
      </div>
    );
  }

  const chartData = data.map((d) => ({
    ...d,
    time: new Date(d.timestamp).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }),
  }));

  return (
    <div className="bg-[#1a1a2e] border border-[#2a2a3e] rounded-xl p-6">
      <h2 className="text-lg font-semibold mb-4">Bankroll Over Time</h2>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3e" />
          <XAxis dataKey="time" stroke="#8888a0" fontSize={12} />
          <YAxis
            stroke="#8888a0"
            fontSize={12}
            tickFormatter={(v) => `$${v}`}
          />
          <Tooltip
            contentStyle={{
              background: "#1a1a2e",
              border: "1px solid #2a2a3e",
              borderRadius: "8px",
              color: "#e4e4ed",
            }}
            formatter={(value: any) => [`$${Number(value).toFixed(2)}`, "Bankroll"]}
          />
          <Line
            type="monotone"
            dataKey="bankroll"
            stroke="#5b7fff"
            strokeWidth={2}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
