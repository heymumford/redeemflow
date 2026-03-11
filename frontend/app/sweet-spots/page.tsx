"use client";

import { useEffect, useState } from "react";
import { getSweetSpots, type SweetSpot } from "@/lib/api";

const RATING_COLORS: Record<string, string> = {
  exceptional: "bg-emerald-100 text-emerald-800",
  excellent: "bg-blue-100 text-blue-800",
  good: "bg-amber-100 text-amber-800",
  fair: "bg-gray-100 text-gray-800",
};

export default function SweetSpotsPage() {
  const [spots, setSpots] = useState<SweetSpot[]>([]);
  const [category, setCategory] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const params: { category?: string } = {};
        if (category) params.category = category;
        const data = await getSweetSpots(params);
        setSpots(data.sweet_spots);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [category]);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Redemption Sweet Spots
        </h1>
        <p className="mt-1 text-gray-500">
          Curated high-value redemptions across all loyalty programs
        </p>
      </div>

      <div className="flex gap-2">
        {["", "flights", "hotels", "experiences", "transfers"].map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${
              category === cat
                ? "bg-rose-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {cat || "All"}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-sm text-gray-500">Loading sweet spots...</div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {spots.map((spot, i) => (
            <div
              key={i}
              className="rounded-lg border border-gray-200 p-5 hover:border-rose-200 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {spot.description}
                  </h3>
                  <p className="mt-0.5 text-sm text-gray-500">
                    {spot.program_name}
                  </p>
                </div>
                <span
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                    RATING_COLORS[spot.rating] ?? "bg-gray-100 text-gray-800"
                  }`}
                >
                  {spot.rating}
                </span>
              </div>
              <div className="mt-3 flex items-baseline gap-3">
                <span className="text-2xl font-bold text-rose-600">
                  {spot.effective_cpp}¢
                </span>
                <span className="text-sm text-gray-500">per point</span>
              </div>
              <div className="mt-2 flex gap-3 text-xs text-gray-500">
                <span>{spot.points_required.toLocaleString()} pts</span>
                <span>${spot.cash_equivalent} value</span>
                {spot.cabin && <span>{spot.cabin}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
