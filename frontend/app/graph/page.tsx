"use client";

import { useEffect, useState } from "react";
import {
  getGraphSummary,
  getProgramConnectivity,
  type GraphSummary,
  type ProgramConnectivity,
} from "@/lib/api";

export default function GraphPage() {
  const [summary, setSummary] = useState<GraphSummary | null>(null);
  const [selectedProgram, setSelectedProgram] = useState<string>("");
  const [connectivity, setConnectivity] =
    useState<ProgramConnectivity | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await getGraphSummary();
        setSummary(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleSelectProgram(program: string) {
    setSelectedProgram(program);
    try {
      const conn = await getProgramConnectivity(program);
      setConnectivity(conn);
    } catch {
      setConnectivity(null);
    }
  }

  if (loading) {
    return <div className="text-sm text-gray-500">Loading graph data...</div>;
  }

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Transfer Graph Explorer
        </h1>
        <p className="mt-1 text-gray-500">
          Explore the loyalty program transfer network
        </p>
      </div>

      {summary && (
        <div className="grid gap-4 sm:grid-cols-4">
          <div className="rounded-lg border border-gray-200 p-4">
            <div className="text-2xl font-bold text-rose-600">
              {summary.total_programs}
            </div>
            <div className="text-sm text-gray-500">Programs</div>
          </div>
          <div className="rounded-lg border border-gray-200 p-4">
            <div className="text-2xl font-bold text-rose-600">
              {summary.total_partnerships}
            </div>
            <div className="text-sm text-gray-500">Partnerships</div>
          </div>
          <div className="rounded-lg border border-gray-200 p-4">
            <div className="text-2xl font-bold text-rose-600">
              {summary.hub_programs.length}
            </div>
            <div className="text-sm text-gray-500">Hub Programs</div>
          </div>
          <div className="rounded-lg border border-gray-200 p-4">
            <div className="text-2xl font-bold text-rose-600">
              {(summary.density * 100).toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500">Network Density</div>
          </div>
        </div>
      )}

      {summary && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-3">
            Hub Programs
          </h2>
          <div className="flex flex-wrap gap-2">
            {summary.hub_programs.map((hub) => (
              <button
                key={hub}
                onClick={() => handleSelectProgram(hub)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
                  selectedProgram === hub
                    ? "bg-rose-600 text-white"
                    : "bg-rose-50 text-rose-700 hover:bg-rose-100"
                }`}
              >
                {hub}
              </button>
            ))}
          </div>
        </div>
      )}

      {connectivity && (
        <div className="rounded-lg border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900">
            {connectivity.program}
            {connectivity.is_hub && (
              <span className="ml-2 rounded-full bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-700">
                Hub
              </span>
            )}
          </h3>
          <div className="mt-4 grid gap-4 sm:grid-cols-3">
            <div>
              <div className="text-xl font-bold">
                {connectivity.outbound_partners}
              </div>
              <div className="text-sm text-gray-500">Outbound Partners</div>
            </div>
            <div>
              <div className="text-xl font-bold">
                {connectivity.inbound_partners}
              </div>
              <div className="text-sm text-gray-500">Inbound Partners</div>
            </div>
            <div>
              <div className="text-xl font-bold">
                {connectivity.total_connections}
              </div>
              <div className="text-sm text-gray-500">Total Connections</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
