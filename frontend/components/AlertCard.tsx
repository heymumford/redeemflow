"use client";

interface Alert {
  id: string;
  alert_type: string;
  priority: string;
  title: string;
  message: string;
  program_code: string;
}

const PRIORITY_STYLES: Record<string, string> = {
  critical: "border-red-300 bg-red-50",
  high: "border-orange-300 bg-orange-50",
  medium: "border-yellow-300 bg-yellow-50",
  low: "border-gray-200 bg-gray-50",
};

const PRIORITY_DOT: Record<string, string> = {
  critical: "bg-red-500",
  high: "bg-orange-500",
  medium: "bg-yellow-500",
  low: "bg-gray-400",
};

interface Props {
  alert: Alert;
}

export default function AlertCard({ alert }: Props) {
  return (
    <div
      className={`rounded-lg border p-4 ${
        PRIORITY_STYLES[alert.priority] ?? "border-gray-200 bg-gray-50"
      }`}
    >
      <div className="flex items-start gap-3">
        <span
          className={`mt-1 h-2.5 w-2.5 shrink-0 rounded-full ${
            PRIORITY_DOT[alert.priority] ?? "bg-gray-400"
          }`}
        />
        <div>
          <h4 className="text-sm font-semibold text-gray-900">{alert.title}</h4>
          <p className="mt-0.5 text-xs text-gray-600">{alert.message}</p>
          <div className="mt-2 flex gap-2 text-xs text-gray-500">
            <span className="rounded bg-white px-1.5 py-0.5 font-mono">
              {alert.program_code}
            </span>
            <span className="rounded bg-white px-1.5 py-0.5">
              {alert.alert_type}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
