"use client";

interface ParsedTransaction {
  date: string;
  amount: number;
  ceiling: number;
  remanent: number;
}

interface ParseResultsTableProps {
  results: ParsedTransaction[];
}

export default function ParseResultsTable({ results }: ParseResultsTableProps) {
  return (
    <div className="overflow-x-auto rounded-xl border border-zinc-200 bg-white shadow-sm">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-zinc-200 bg-zinc-50 text-xs uppercase tracking-wide text-zinc-500">
            <th className="px-4 py-3">Date</th>
            <th className="px-4 py-3 text-right">Amount</th>
            <th className="px-4 py-3 text-right">Ceiling</th>
            <th className="px-4 py-3 text-right">Savings</th>
            <th className="px-4 py-3 min-w-[160px]">Round-Up</th>
          </tr>
        </thead>
        <tbody>
          {results.map((txn, idx) => {
            const pct = txn.ceiling > 0 ? (txn.remanent / txn.ceiling) * 100 : 0;
            return (
              <tr
                key={idx}
                className="border-b border-zinc-100 last:border-0 hover:bg-zinc-50 transition-colors"
              >
                <td className="px-4 py-3 font-mono text-zinc-700">{txn.date}</td>
                <td className="px-4 py-3 text-right font-medium text-zinc-900">
                  ₹{txn.amount.toFixed(2)}
                </td>
                <td className="px-4 py-3 text-right text-blue-600">₹{txn.ceiling.toFixed(2)}</td>
                <td className="px-4 py-3 text-right font-semibold text-emerald-600">
                  ₹{txn.remanent.toFixed(2)}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="h-2.5 flex-1 rounded-full bg-zinc-100">
                      <div
                        className="h-2.5 rounded-full bg-emerald-500 transition-all duration-500"
                        style={{ width: `${Math.min(pct, 100)}%` }}
                      />
                    </div>
                    <span className="w-10 text-right text-xs text-zinc-400">{pct.toFixed(0)}%</span>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
