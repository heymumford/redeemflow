"use client";

interface SavingsData {
  total_travel_value: string;
  total_cash_back_value: string;
  total_opportunity_cost: string;
  total_points: number;
  weighted_avg_cpp: string;
  best_program: string | null;
  worst_program: string | null;
}

interface Props {
  savings: SavingsData;
}

export default function SavingsSummary({ savings }: Props) {
  return (
    <div className="rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900">Savings Analysis</h3>
      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <div>
          <div className="text-2xl font-bold text-emerald-600">
            ${savings.total_travel_value}
          </div>
          <div className="text-sm text-gray-500">Travel Value</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-gray-600">
            ${savings.total_cash_back_value}
          </div>
          <div className="text-sm text-gray-500">Cash Back Value</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-rose-600">
            ${savings.total_opportunity_cost}
          </div>
          <div className="text-sm text-gray-500">Opportunity Cost</div>
        </div>
      </div>
      <div className="mt-4 flex gap-6 text-sm text-gray-600">
        <span>
          <span className="font-medium">{savings.total_points.toLocaleString()}</span>{" "}
          total points
        </span>
        <span>
          <span className="font-medium">{savings.weighted_avg_cpp}¢</span>{" "}
          weighted avg CPP
        </span>
        {savings.best_program && (
          <span>
            Best:{" "}
            <span className="font-medium text-emerald-600">
              {savings.best_program}
            </span>
          </span>
        )}
      </div>
    </div>
  );
}
