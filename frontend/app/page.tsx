"use client";

import { useState } from "react";
import ExpenseForm from "@/components/demo/ExpenseForm";
import ParseResultsTable from "@/components/demo/ParseResultsTable";
import PerformanceMonitor from "@/components/demo/PerformanceMonitor";
import ReturnsComparison from "@/components/demo/ReturnsComparison";
import SummaryCard from "@/components/demo/SummaryCard";

interface Expense {
  date: string;
  amount: string;
}

interface ParsedTransaction {
  date: string;
  amount: number;
  ceiling: number;
  remanent: number;
}

const SAMPLE_EXPENSES: Expense[] = [
  { date: "2023-10-12 14:23:00", amount: "250" },
  { date: "2023-02-28 09:15:00", amount: "375" },
  { date: "2023-07-01 12:00:00", amount: "620" },
  { date: "2023-12-17 18:30:00", amount: "480" },
];

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5477";

export default function Home() {
  const [expenses, setExpenses] = useState<Expense[]>([{ date: "", amount: "" }]);
  const [results, setResults] = useState<ParsedTransaction[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCalculate = async () => {
    setLoading(true);
    setError(null);
    setResults(null);

    const payload = expenses
      .filter((e) => e.date && e.amount)
      .map((e) => ({ date: e.date, amount: parseFloat(e.amount) }));

    try {
      const res = await fetch(`${API_URL}/blackrock/challenge/v1/transactions:parse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        throw new Error(`API returned ${res.status}`);
      }

      const data: ParsedTransaction[] = await res.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch");
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = () => {
    setExpenses([...SAMPLE_EXPENSES]);
    setResults(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-zinc-50">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div>
            <h1 className="text-xl font-bold text-zinc-900">PennyWise</h1>
            <p className="text-sm text-zinc-500">Expense Round-Up Savings Calculator</p>
          </div>
          <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700">
            Demo
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-6 py-8">
        <ExpenseForm
          expenses={expenses}
          onExpensesChange={setExpenses}
          onCalculate={handleCalculate}
          onLoadSample={handleLoadSample}
          loading={loading}
        />

        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {results && (
          <>
            <SummaryCard results={results} />
            <ParseResultsTable results={results} />
          </>
        )}

        <hr className="border-zinc-200" />

        <ReturnsComparison expenses={expenses} />

        <hr className="border-zinc-200" />

        <PerformanceMonitor />
      </main>
    </div>
  );
}
