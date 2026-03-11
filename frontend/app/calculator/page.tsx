"use client";

import { useState } from "react";
import { getTopPaths, getValuation, type PathResult } from "@/lib/api";

export default function CalculatorPage() {
  const [program, setProgram] = useState("chase-ur");
  const [points, setPoints] = useState(100000);
  const [paths, setPaths] = useState<PathResult[]>([]);
  const [valuation, setValuation] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCalculate() {
    setLoading(true);
    setError(null);
    try {
      const [pathData, valData] = await Promise.all([
        getTopPaths(program, points),
        getValuation(program).catch(() => null),
      ]);
      setPaths(pathData.paths);
      if (valData) {
        setValuation(valData.aggregated_cpp);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to calculate");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Points Calculator</h1>
        <p className="mt-1 text-gray-500">
          Find the best transfer paths for your points
        </p>
      </div>

      <div className="flex gap-4 items-end">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Program
          </label>
          <select
            value={program}
            onChange={(e) => setProgram(e.target.value)}
            className="mt-1 block rounded-md border border-gray-300 px-3 py-2 text-sm"
          >
            <option value="chase-ur">Chase Ultimate Rewards</option>
            <option value="amex-mr">Amex Membership Rewards</option>
            <option value="citi-ty">Citi ThankYou</option>
            <option value="capital-one">Capital One Miles</option>
            <option value="bilt">Bilt Rewards</option>
            <option value="wells-fargo">Wells Fargo Rewards</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Points
          </label>
          <input
            type="number"
            value={points}
            onChange={(e) => setPoints(Number(e.target.value))}
            className="mt-1 block rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
        </div>
        <button
          onClick={handleCalculate}
          disabled={loading}
          className="rounded-md bg-rose-600 px-4 py-2 text-sm font-medium text-white hover:bg-rose-700 disabled:opacity-50"
        >
          {loading ? "Calculating..." : "Calculate"}
        </button>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {valuation && (
        <div className="rounded-md bg-rose-50 p-4">
          <p className="text-sm text-gray-700">
            <span className="font-medium">Baseline CPP:</span> {valuation}¢ per
            point
          </p>
        </div>
      )}

      {paths.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Top Transfer Paths
          </h2>
          <div className="space-y-3">
            {paths.map((path, i) => (
              <div
                key={i}
                className="rounded-lg border border-gray-200 p-4 hover:border-rose-200"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm text-gray-800">
                    {path.route}
                  </span>
                  <span className="rounded-full bg-rose-100 px-3 py-1 text-sm font-bold text-rose-700">
                    {path.effective_cpp}¢/pt
                  </span>
                </div>
                <div className="mt-2 flex gap-4 text-xs text-gray-500">
                  <span>{path.hops} hop{path.hops !== 1 ? "s" : ""}</span>
                  <span>{path.source_points_needed.toLocaleString()} pts needed</span>
                  <span>Efficiency: {path.efficiency_score}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
