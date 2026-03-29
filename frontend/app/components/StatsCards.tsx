"use client";

interface PortfolioData {
  bankroll: number;
  initial_bankroll: number;
  total_wins: number;
  total_losses: number;
  profit: number;
  roi: number;
  win_rate: number;
}

export default function StatsCards({ data }: { data: PortfolioData | null }) {
  if (!data) return null;

  const cards = [
    {
      label: "Bankroll",
      value: `$${data.bankroll.toFixed(2)}`,
      color: "#5b7fff",
    },
    {
      label: "Profit / Loss",
      value: `${data.profit >= 0 ? "+" : ""}$${data.profit.toFixed(2)}`,
      color: data.profit >= 0 ? "#00d4aa" : "#ff4757",
    },
    {
      label: "ROI",
      value: `${data.roi >= 0 ? "+" : ""}${data.roi.toFixed(1)}%`,
      color: data.roi >= 0 ? "#00d4aa" : "#ff4757",
    },
    {
      label: "Win Rate",
      value: `${data.win_rate.toFixed(1)}%`,
      color: "#ffc048",
    },
    {
      label: "Wins",
      value: data.total_wins.toString(),
      color: "#00d4aa",
    },
    {
      label: "Losses",
      value: data.total_losses.toString(),
      color: "#ff4757",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-[#1a1a2e] border border-[#2a2a3e] rounded-xl p-4"
        >
          <div className="text-xs text-[#8888a0] uppercase tracking-wider mb-1">
            {card.label}
          </div>
          <div className="text-2xl font-bold" style={{ color: card.color }}>
            {card.value}
          </div>
        </div>
      ))}
    </div>
  );
}
