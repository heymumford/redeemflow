interface MobileCardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  accentColor?: string;
  onClick?: () => void;
  className?: string;
}

export default function MobileCard({
  children,
  title,
  subtitle,
  accentColor = "rose",
  onClick,
  className = "",
}: MobileCardProps) {
  const borderColor = `border-l-${accentColor}-500`;
  const interactive = onClick ? "cursor-pointer hover:shadow-md active:scale-[0.98] transition-all" : "";

  return (
    <div
      className={`bg-white rounded-xl border border-gray-100 shadow-sm p-4 sm:p-5 border-l-4 ${borderColor} ${interactive} ${className}`}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === "Enter" || e.key === " ") onClick(); } : undefined}
    >
      {(title || subtitle) && (
        <div className="mb-3">
          {title && <h3 className="text-sm sm:text-base font-semibold text-gray-900">{title}</h3>}
          {subtitle && <p className="text-xs sm:text-sm text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
}
