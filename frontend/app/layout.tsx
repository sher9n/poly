import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PolyTrader - Paper Trading Dashboard",
  description: "Polymarket paper trading with AI research",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <nav className="border-b border-[#2a2a3e] px-6 py-4">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <a href="/" className="text-xl font-bold text-[#5b7fff]">
              PolyTrader
            </a>
            <div className="flex gap-6">
              <a href="/" className="text-[#8888a0] hover:text-white transition">
                Dashboard
              </a>
              <a href="/events" className="text-[#8888a0] hover:text-white transition">
                Events
              </a>
              <a href="/trades" className="text-[#8888a0] hover:text-white transition">
                Trades
              </a>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
