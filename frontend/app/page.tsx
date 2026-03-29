"use client";

import { useEffect, useState, useCallback } from "react";
import StatsCards from "./components/StatsCards";
import BankrollChart from "./components/BankrollChart";
import TradeList from "./components/TradeList";

export default function Dashboard() {
  const [portfolio, setPortfolio] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [trades, setTrades] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [pRes, hRes, tRes] = await Promise.all([
        fetch("/api/portfolio"),
        fetch("/api/portfolio/history"),
        fetch("/api/trades"),
      ]);
      setPortfolio(await pRes.json());
      setHistory(await hRes.json());
      setTrades(await tRes.json());
    } catch (e) {
      console.error("Failed to fetch data:", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleResolve = async (tradeId: number, outcome: string) => {
    await fetch(`/api/trades/${tradeId}/resolve?outcome=${outcome}`, {
      method: "POST",
    });
    fetchData();
  };

  if (loading) {
    return (
      <div className="text-center py-20 text-[#8888a0]">
        Loading dashboard...
      </div>
    );
  }

  const openTrades = trades.filter((t: any) => t.status === "open");
  const recentResolved = trades
    .filter((t: any) => t.status !== "open")
    .slice(0, 5);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex gap-3">
          <a
            href="/events"
            className="px-4 py-2 bg-[#5b7fff] text-white rounded-lg hover:bg-[#4a6eee] transition text-sm font-medium"
          >
            Scan Events
          </a>
        </div>
      </div>

      <StatsCards data={portfolio} />
      <BankrollChart data={history} />

      <div className="grid md:grid-cols-2 gap-6">
        <div>
          <h2 className="text-lg font-semibold mb-3">
            Open Positions ({openTrades.length})
          </h2>
          <TradeList trades={openTrades} onResolve={handleResolve} />
        </div>
        <div>
          <h2 className="text-lg font-semibold mb-3">Recent Results</h2>
          <TradeList trades={recentResolved} />
        </div>
      </div>
    </div>
  );
}
