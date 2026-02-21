"use client";

interface Expense {
  date: string;
  amount: string;
}

interface ExpenseFormProps {
  expenses: Expense[];
  onExpensesChange: (expenses: Expense[]) => void;
  onCalculate: () => void;
  onLoadSample: () => void;
  loading: boolean;
}

export default function ExpenseForm({
  expenses,
  onExpensesChange,
  onCalculate,
  onLoadSample,
  loading,
}: ExpenseFormProps) {
  const updateExpense = (index: number, field: keyof Expense, value: string) => {
    const updated = [...expenses];
    updated[index] = { ...updated[index], [field]: value };
    onExpensesChange(updated);
  };

  const addExpense = () => {
    onExpensesChange([...expenses, { date: "", amount: "" }]);
  };

  const removeExpense = (index: number) => {
    onExpensesChange(expenses.filter((_, i) => i !== index));
  };

  const hasExpenses = expenses.some((e) => e.date && e.amount);

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-900">Expenses</h2>
        <button
          type="button"
          onClick={onLoadSample}
          className="rounded-lg bg-zinc-100 px-3 py-1.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-zinc-200"
        >
          Load Sample Data
        </button>
      </div>

      <div className="space-y-3">
        {expenses.map((expense, idx) => (
          <div key={idx} className="flex items-center gap-3">
            <input
              type="text"
              placeholder="2023-10-12 14:23:00"
              value={expense.date}
              onChange={(e) => updateExpense(idx, "date", e.target.value)}
              className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 placeholder-zinc-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <input
              type="number"
              placeholder="Amount"
              value={expense.amount}
              onChange={(e) => updateExpense(idx, "amount", e.target.value)}
              className="w-28 rounded-lg border border-zinc-300 px-3 py-2 text-sm text-zinc-900 placeholder-zinc-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <button
              type="button"
              onClick={() => removeExpense(idx)}
              className="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-red-50 hover:text-red-500"
              aria-label="Remove expense"
            >
              ✕
            </button>
          </div>
        ))}
      </div>

      <div className="mt-4 flex gap-3">
        <button
          type="button"
          onClick={addExpense}
          className="rounded-lg border border-dashed border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-600 transition-colors hover:border-zinc-400 hover:text-zinc-800"
        >
          + Add Expense
        </button>
        <button
          type="button"
          onClick={onCalculate}
          disabled={loading || !hasExpenses}
          className="rounded-lg bg-emerald-600 px-6 py-2 text-sm font-semibold text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </div>
    </div>
  );
}
