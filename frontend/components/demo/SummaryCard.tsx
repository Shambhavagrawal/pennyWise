"use client";

interface ParsedTransaction {
  date: string;
  amount: number;
  ceiling: number;
  remanent: number;
}

interface SummaryCardProps {
  results: ParsedTransaction[];
}

export default function SummaryCard({ results }: SummaryCardProps) {
  const totalAmount = results.reduce((sum, r) => sum + r.amount, 0);
  const totalCeiling = results.reduce((sum, r) => sum + r.ceiling, 0);
  const totalSavings = results.reduce((sum, r) => sum + r.remanent, 0);

  const cards = [
    { label: "Total Spent", value: totalAmount, color: "text-zinc-900" },
    { label: "Total Ceiling", value: totalCeiling, color: "text-blue-600" },
    { label: "Total Savings", value: totalSavings, color: "text-emerald-600" },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {cards.map((card) => (
        <div key={card.label} className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-zinc-500">{card.label}</p>
          <p className={`mt-1 text-2xl font-bold ${card.color}`}>₹{card.value.toFixed(2)}</p>
        </div>
      ))}
    </div>
  );
}
