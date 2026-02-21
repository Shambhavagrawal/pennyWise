"use client";

import { useEffect, useRef, useState } from "react";

interface PerformanceData {
  time: string;
  memory: string;
  threads: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5477";
const POLL_INTERVAL = 5000;

export default function PerformanceMonitor() {
  const [data, setData] = useState<PerformanceData | null>(null);
  const [offline, setOffline] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchPerformance = async () => {
    try {
      const res = await fetch(`${API_URL}/blackrock/challenge/v1/performance`);
      if (!res.ok) throw new Error("API error");
      const json: PerformanceData = await res.json();
      setData(json);
      setOffline(false);
    } catch {
      setOffline(true);
    }
  };

  const startPolling = () => {
    if (intervalRef.current) return;
    fetchPerformance();
    intervalRef.current = setInterval(fetchPerformance, POLL_INTERVAL);
  };

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  useEffect(() => {
    startPolling();

    const handleVisibility = () => {
      if (document.hidden) {
        stopPolling();
      } else {
        startPolling();
      }
    };

    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      stopPolling();
      document.removeEventListener("visibilitychange", handleVisibility);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!data && !offline) {
    return (
      <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
        <p className="text-center text-sm text-zinc-400">Loading server metrics...</p>
      </div>
    );
  }

  if (offline && !data) {
    return (
      <div className="rounded-xl border border-orange-200 bg-orange-50 p-4 shadow-sm">
        <p className="text-center text-sm text-orange-600">Server offline</p>
      </div>
    );
  }

  const stats = [
    { label: "Uptime", value: data?.time ?? "--", icon: "clock" },
    { label: "Memory", value: data ? `${data.memory} MB` : "--", icon: "memory" },
    { label: "Threads", value: data ? `${data.threads}` : "--", icon: "threads" },
  ];

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-700">Server Performance</h3>
        <span
          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ${
            offline ? "bg-orange-100 text-orange-600" : "bg-emerald-100 text-emerald-600"
          }`}
        >
          <span
            className={`inline-block h-1.5 w-1.5 rounded-full ${
              offline ? "bg-orange-400" : "bg-emerald-400"
            }`}
          />
          {offline ? "Offline" : "Live"}
        </span>
      </div>
      <div className="grid grid-cols-3 gap-4">
        {stats.map((stat) => (
          <div key={stat.label} className="text-center">
            <p className="text-xs font-medium text-zinc-400">{stat.label}</p>
            <p className="mt-1 font-mono text-sm font-semibold text-zinc-800">{stat.value}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
