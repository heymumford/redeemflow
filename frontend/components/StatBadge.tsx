interface StatBadgeProps {
  label: string;
  value: string;
  trend?: "up" | "down" | "neutral";
  size?: "sm" | "md" | "lg";
  className?: string;
}

const trendColors = {
  up: "text-green-600",
  down: "text-red-600",
  neutral: "text-gray-600",
};

const trendIcons = {
  up: "↑",
  down: "↓",
  neutral: "→",
};

const sizes = {
  sm: { value: "text-lg sm:text-xl", label: "text-xs" },
  md: { value: "text-xl sm:text-2xl", label: "text-xs sm:text-sm" },
  lg: { value: "text-2xl sm:text-3xl", label: "text-sm" },
};

export default function StatBadge({
  label,
  value,
  trend,
  size = "md",
  className = "",
}: StatBadgeProps) {
  const sizeClasses = sizes[size];
  const trendColor = trend ? trendColors[trend] : "";

  return (
    <div className={`text-center p-3 sm:p-4 ${className}`}>
      <div className={`font-bold ${sizeClasses.value} ${trendColor || "text-gray-900"}`}>
        {trend && <span className="mr-1">{trendIcons[trend]}</span>}
        {value}
      </div>
      <div className={`${sizeClasses.label} text-gray-500 mt-1`}>{label}</div>
    </div>
  );
}
