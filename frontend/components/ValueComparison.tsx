"use client";

interface ValueRow {
  label: string;
  value: string;
  highlight?: boolean;
}

interface Props {
  title: string;
  rows: ValueRow[];
  recommendation?: string;
}

export default function ValueComparison({ title, rows, recommendation }: Props) {
  return (
    <div className="rounded-lg border border-gray-200 p-5">
      <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
        {title}
      </h3>
      <div className="mt-3 space-y-2">
        {rows.map((row, i) => (
          <div
            key={i}
            className={`flex items-center justify-between text-sm ${
              row.highlight
                ? "font-semibold text-rose-700"
                : "text-gray-600"
            }`}
          >
            <span>{row.label}</span>
            <span className="font-mono">{row.value}</span>
          </div>
        ))}
      </div>
      {recommendation && (
        <div className="mt-3 rounded-md bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {recommendation}
        </div>
      )}
    </div>
  );
}
