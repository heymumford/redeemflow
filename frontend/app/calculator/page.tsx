"use client";

import { useState } from "react";
import ProgramSelector from "@/components/ProgramSelector";
import ValueComparison from "@/components/ValueComparison";
import { getTopPaths, getValuation, type PathResult } from "@/lib/api";

interface ValuationData {
  aggregated_cpp: string;
  strategy: string;
  confidence: string;
  source_count: number;
}

export default function CalculatorPage() {
  const [program, setProgram] = useState("chase-ur");
  const [points, setPoints] = useState(100000);
  const [paths, setPaths] = useState<PathResult[]>([]);
  const [valuation, setValuation] = useState<ValuationData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [calculated, setCalculated] = useState(false);

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
        setValuation({
          aggregated_cpp: valData.aggregated_cpp,
          strategy: valData.strategy,
          confidence: valData.confidence,
          source_count: valData.source_count,
        });
      }
      setCalculated(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to calculate");
    } finally {
      setLoading(false);
    }
  }

  const cashBackValue = valuation
    ? ((points * parseFloat(valuation.aggregated_cpp)) / 100).toFixed(2)
    : null;

  const bestPath = paths.length > 0 ? paths[0] : null;
  const bestPathValue = bestPath
    ? ((points * parseFloat(bestPath.effective_cpp)) / 100).toFixed(2)
    : null;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Points Calculator</h1>
        <p className="mt-1 text-gray-500">
          Calculate the value of your points and find optimal transfer paths
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Program
          </label>
          <ProgramSelector selected={program} onSelect={setProgram} />
        </div>

        <div className="flex items-end gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700">
              Points Balance
            </label>
            <input
              type="number"
              value={points}
              onChange={(e) => setPoints(Number(e.target.value))}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-rose-500 focus:ring-rose-500"
              min={0}
              step={1000}
            />
          </div>
          <button
            onClick={handleCalculate}
            disabled={loading || points <= 0}
            className="rounded-md bg-rose-600 px-6 py-2 text-sm font-medium text-white hover:bg-rose-700 disabled:opacity-50"
          >
            {loading ? "Calculating..." : "Calculate Value"}
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {calculated && valuation && (
        <div className="grid gap-4 sm:grid-cols-2">
          <ValueComparison
            title="Cash Back Value"
            rows={[
              { label: "Baseline CPP", value: `${valuation.aggregated_cpp}¢` },
              { label: "Strategy", value: valuation.strategy },
              { label: "Confidence", value: valuation.confidence },
              { label: "Sources", value: String(valuation.source_count) },
              {
                label: "Cash Value",
                value: cashBackValue ? `$${cashBackValue}` : "N/A",
                highlight: true,
              },
            ]}
            recommendation="Statement credit or cash back at baseline rate"
          />

          {bestPath && bestPathValue && (
            <ValueComparison
              title="Best Transfer Path"
              rows={[
                { label: "Route", value: bestPath.route },
                { label: "Effective CPP", value: `${bestPath.effective_cpp}¢` },
                { label: "Hops", value: String(bestPath.hops) },
                {
                  label: "Points Needed",
                  value: bestPath.source_points_needed.toLocaleString(),
                },
                {
                  label: "Travel Value",
                  value: `$${bestPathValue}`,
                  highlight: true,
                },
              ]}
              recommendation={
                cashBackValue && bestPathValue
                  ? `Transfer path yields ${(
                      parseFloat(bestPathValue) / parseFloat(cashBackValue)
                    ).toFixed(1)}x more value than cash back`
                  : undefined
              }
            />
          )}
        </div>
      )}

      {paths.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">
            All Transfer Paths ({paths.length})
          </h2>
          <div className="space-y-3">
            {paths.map((path, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg border border-gray-200 p-4 hover:border-rose-200 transition-colors"
              >
                <div>
                  <span className="font-mono text-sm text-gray-800">
                    {path.route}
                  </span>
                  <div className="mt-1 flex gap-4 text-xs text-gray-500">
                    <span>
                      {path.hops} hop{path.hops !== 1 ? "s" : ""}
                    </span>
                    <span>
                      {path.source_points_needed.toLocaleString()} pts
                    </span>
                    <span>Efficiency: {path.efficiency_score}</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="rounded-full bg-rose-100 px-3 py-1 text-sm font-bold text-rose-700">
                    {path.effective_cpp}¢/pt
                  </span>
                  <div className="mt-1 text-xs text-gray-500">
                    {path.redemption}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
