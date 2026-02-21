import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import Home from "@/app/page";

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
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
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResults,
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
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
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
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResults,
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
});
