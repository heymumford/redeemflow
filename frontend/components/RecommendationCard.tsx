import type { Recommendation } from "@/lib/api";

function formatProgramName(code: string): string {
  return code
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

interface RecommendationCardProps {
  recommendation: Recommendation;
}

export default function RecommendationCard({
  recommendation,
}: RecommendationCardProps) {
  const cppGain = parseFloat(recommendation.cpp_gain);

  return (
    <div className="rounded-2xl border border-rose-100 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <div className="text-xs font-medium uppercase tracking-wider text-rose-400">
            {formatProgramName(recommendation.program_code)}
          </div>
          <div className="mt-1 text-lg font-semibold capitalize text-gray-900">
            {recommendation.action}
          </div>
        </div>
        <span
          className={`rounded-full px-3 py-1 text-xs font-semibold ${
            cppGain > 0
              ? "bg-emerald-50 text-emerald-700"
              : "bg-gray-100 text-gray-600"
          }`}
        >
          {cppGain > 0 ? "+" : ""}
          {recommendation.cpp_gain} cpp
        </span>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-gray-600">
        {recommendation.rationale}
      </p>
      <div className="mt-4 flex items-center justify-between border-t border-rose-50 pt-3">
        <span className="text-sm text-gray-500">
          {recommendation.points_involved.toLocaleString()} points
        </span>
        <button className="rounded-full bg-rose-500 px-4 py-1.5 text-xs font-semibold text-white transition-colors hover:bg-rose-600">
          Take Action
        </button>
      </div>
    </div>
  );
}
