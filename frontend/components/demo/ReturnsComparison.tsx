"use client";

import { useState } from "react";

interface SavingsByDate {
  start: string;
  end: string;
  amount: number;
  profit: number;
  taxBenefit: number;
}

interface ReturnsResult {
  totalTransactionAmount: number;
  totalCeiling: number;
  savingsByDates: SavingsByDate[];
}

interface Expense {
  date: string;
  amount: string;
}

interface ReturnsComparisonProps {
  expenses: Expense[];
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5477";

const SAMPLE_Q = [{ fixed: 0, start: "2023-07-01 00:00:00", end: "2023-07-31 23:59:59" }];
const SAMPLE_P = [{ extra: 25, start: "2023-10-01 08:00:00", end: "2023-12-31 19:59:59" }];
const SAMPLE_K = [
  { start: "2023-03-01 00:00:00", end: "2023-11-30 23:59:59" },
  { start: "2023-01-01 00:00:00", end: "2023-12-31 23:59:59" },
];

export default function ReturnsComparison({ expenses }: ReturnsComparisonProps) {
  const [age, setAge] = useState("29");
  const [wage, setWage] = useState("50000");
  const [inflation, setInflation] = useState("5.5");
  const [nps, setNps] = useState<ReturnsResult | null>(null);
  const [index, setIndex] = useState<ReturnsResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    const txns = expenses
      .filter((e) => e.date && e.amount)
      .map((e) => ({ date: e.date, amount: parseFloat(e.amount) }));

    if (txns.length === 0) {
      setError("Add transactions in the expense form above first");
      return;
    }

    setLoading(true);
    setError(null);
    setNps(null);
    setIndex(null);

    const payload = {
      age: parseInt(age),
      wage: parseFloat(wage),
      inflation: parseFloat(inflation),
      q: SAMPLE_Q,
      p: SAMPLE_P,
      k: SAMPLE_K,
      transactions: txns,
    };

    try {
      const [npsRes, indexRes] = await Promise.all([
        fetch(`${API_URL}/blackrock/challenge/v1/returns:nps`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
        fetch(`${API_URL}/blackrock/challenge/v1/returns:index`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }),
      ]);

      if (!npsRes.ok || !indexRes.ok) {
        throw new Error(`API error: NPS=${npsRes.status}, Index=${indexRes.status}`);
      }

      setNps(await npsRes.json());
      setIndex(await indexRes.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch");
    } finally {
      setLoading(false);
    }
  };

  const totalProfit = (r: ReturnsResult) => r.savingsByDates.reduce((s, d) => s + d.profit, 0);

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-zinc-900">NPS vs Index Fund Comparison</h2>

      <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">Age</label>
            <input
              type="number"
              value={age}
              onChange={(e) => setAge(e.target.value)}
              className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">Monthly Wage (₹)</label>
            <input
              type="number"
              value={wage}
              onChange={(e) => setWage(e.target.value)}
              className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-zinc-500">Inflation (%)</label>
            <input
              type="number"
              step="0.1"
              value={inflation}
              onChange={(e) => setInflation(e.target.value)}
              className="w-full rounded-lg border border-zinc-200 px-3 py-2 text-sm"
            />
          </div>
        </div>

        <button
          onClick={handleCompare}
          disabled={loading}
          className="mt-4 rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Comparing..." : "Compare Returns"}
        </button>
      </div>

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {nps && index && (
        <>
          {/* Summary comparison */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
              <p className="text-sm font-medium text-blue-600">NPS (7.11%)</p>
              <p className="mt-1 text-2xl font-bold text-blue-900">
                ₹{totalProfit(nps).toFixed(2)}
              </p>
              <p className="mt-1 text-xs text-blue-500">Total inflation-adjusted profit</p>
            </div>
            <div className="rounded-xl border border-purple-200 bg-purple-50 p-5">
              <p className="text-sm font-medium text-purple-600">Index Fund (14.49%)</p>
              <p className="mt-1 text-2xl font-bold text-purple-900">
                ₹{totalProfit(index).toFixed(2)}
              </p>
              <p className="mt-1 text-xs text-purple-500">Total inflation-adjusted profit</p>
            </div>
          </div>

          {/* Per k-period breakdown */}
          <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white shadow-sm">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500">
                  <th className="px-4 py-3">Period</th>
                  <th className="px-4 py-3 text-right">Savings</th>
                  <th className="px-4 py-3 text-right">NPS Profit</th>
                  <th className="px-4 py-3 text-right">Index Profit</th>
                  <th className="px-4 py-3 text-right">Tax Benefit</th>
                  <th className="px-4 py-3">Winner</th>
                </tr>
              </thead>
              <tbody>
                {nps.savingsByDates.map((npsRow, i) => {
                  const idxRow = index.savingsByDates[i];
                  const npsWins = npsRow.profit + npsRow.taxBenefit > idxRow.profit;
                  const winner = npsWins ? "NPS" : "Index";
                  return (
                    <tr
                      key={i}
                      className="border-b border-zinc-100 last:border-0 hover:bg-zinc-50 transition-colors"
                    >
                      <td className="px-4 py-3 font-mono text-xs text-zinc-600">
                        {npsRow.start.slice(0, 10)} — {npsRow.end.slice(0, 10)}
                      </td>
                      <td className="px-4 py-3 text-right text-zinc-700">
                        ₹{npsRow.amount.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-blue-600">
                        ₹{npsRow.profit.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right font-medium text-purple-600">
                        ₹{idxRow.profit.toFixed(2)}
                      </td>
                      <td className="px-4 py-3 text-right text-emerald-600">
                        ₹{npsRow.taxBenefit.toFixed(2)}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                            npsWins ? "bg-blue-100 text-blue-700" : "bg-purple-100 text-purple-700"
                          }`}
                        >
                          {winner}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Totals row */}
          <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-500">
                Transactions: ₹{nps.totalTransactionAmount.toFixed(2)} | Ceiling: ₹
                {nps.totalCeiling.toFixed(2)}
              </span>
              <span className="text-xs text-zinc-400">
                Investment period: {Math.max(60 - parseInt(age), 5)} years
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
