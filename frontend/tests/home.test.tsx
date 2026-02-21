import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Home from "@/app/page";

const mockFetch = vi.fn();
global.fetch = mockFetch;

const PERF_DATA = { time: "00:00:05.000", memory: "25.11", threads: 8 };

beforeEach(() => {
  mockFetch.mockReset();
  // Default: performance endpoint returns data, everything else 404
  mockFetch.mockImplementation((url: string) => {
    if (url.includes("/performance")) {
      return Promise.resolve({ ok: true, json: async () => PERF_DATA });
    }
    return Promise.resolve({ ok: false, status: 404 });
  });
});

describe("Home page", () => {
  it("renders the expense form with inputs", () => {
    render(<Home />);
    expect(screen.getByText("PennyWise")).toBeDefined();
    expect(screen.getByText("Expenses")).toBeDefined();
    expect(screen.getByText("+ Add Expense")).toBeDefined();
    expect(screen.getByText("Calculate")).toBeDefined();
  });

  it("loads sample data when button is clicked", () => {
    render(<Home />);
    fireEvent.click(screen.getByText("Load Sample Data"));
    const inputs = screen.getAllByPlaceholderText("Amount");
    expect(inputs).toHaveLength(4);
  });

  it("shows results after successful calculate", async () => {
    const mockResults = [
      { date: "2023-10-12 14:23:00", amount: 250, ceiling: 300, remanent: 50 },
      { date: "2023-02-28 09:15:00", amount: 375, ceiling: 400, remanent: 25 },
    ];
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/performance")) {
        return Promise.resolve({ ok: true, json: async () => PERF_DATA });
      }
      return Promise.resolve({ ok: true, json: async () => mockResults });
    });

    render(<Home />);
    fireEvent.click(screen.getByText("Load Sample Data"));
    fireEvent.click(screen.getByText("Calculate"));

    await waitFor(() => {
      expect(screen.getByText("Total Spent")).toBeDefined();
      expect(screen.getByText("Total Savings")).toBeDefined();
    });
  });

  it("shows error on API failure", async () => {
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/performance")) {
        return Promise.resolve({ ok: true, json: async () => PERF_DATA });
      }
      return Promise.resolve({ ok: false, status: 500 });
    });

    render(<Home />);
    fireEvent.click(screen.getByText("Load Sample Data"));
    fireEvent.click(screen.getByText("Calculate"));

    await waitFor(() => {
      expect(screen.getByText("API returned 500")).toBeDefined();
    });
  });

  it("summary card computes correct totals", async () => {
    const mockResults = [
      { date: "2023-10-12 14:23:00", amount: 250, ceiling: 300, remanent: 50 },
      { date: "2023-02-28 09:15:00", amount: 375, ceiling: 400, remanent: 25 },
    ];
    mockFetch.mockImplementation((url: string) => {
      if (url.includes("/performance")) {
        return Promise.resolve({ ok: true, json: async () => PERF_DATA });
      }
      return Promise.resolve({ ok: true, json: async () => mockResults });
    });

    render(<Home />);
    fireEvent.click(screen.getByText("Load Sample Data"));
    fireEvent.click(screen.getByText("Calculate"));

    await waitFor(() => {
      expect(screen.getByText("₹625.00")).toBeDefined(); // total spent
      expect(screen.getByText("₹700.00")).toBeDefined(); // total ceiling
      expect(screen.getByText("₹75.00")).toBeDefined(); // total savings
    });
  });

  it("renders performance monitor widget", async () => {
    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText("Server Performance")).toBeDefined();
      expect(screen.getByText("00:00:05.000")).toBeDefined();
      expect(screen.getByText("25.11 MB")).toBeDefined();
      expect(screen.getByText("8")).toBeDefined();
      expect(screen.getByText("Live")).toBeDefined();
    });
  });
});
