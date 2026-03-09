import type { Balance } from "@/lib/api";

function formatProgramName(code: string): string {
  return code
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

function formatPoints(points: number): string {
  return points.toLocaleString();
}

interface PortfolioCardProps {
  balance: Balance;
}

export default function PortfolioCard({ balance }: PortfolioCardProps) {
  return (
    <div className="rounded-2xl border border-rose-100 bg-white p-6 shadow-sm transition-shadow hover:shadow-md">
      <div className="mb-1 text-xs font-medium uppercase tracking-wider text-rose-400">
        {formatProgramName(balance.program_code)}
      </div>
      <div className="text-3xl font-bold text-gray-900">
        {formatPoints(balance.points)}
      </div>
      <div className="mt-1 text-sm text-gray-500">points</div>
      <div className="mt-4 border-t border-rose-50 pt-3 text-sm font-medium text-rose-600">
        ${balance.estimated_value_dollars} estimated value
      </div>
    </div>
  );
}
