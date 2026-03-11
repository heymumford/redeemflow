interface ResponsiveGridProps {
  children: React.ReactNode;
  columns?: { sm?: number; md?: number; lg?: number };
  gap?: string;
  className?: string;
}

export default function ResponsiveGrid({
  children,
  columns = { sm: 1, md: 2, lg: 3 },
  gap = "gap-4 sm:gap-6",
  className = "",
}: ResponsiveGridProps) {
  const gridCols = [
    columns.sm === 1 ? "grid-cols-1" : `grid-cols-${columns.sm}`,
    columns.md ? `md:grid-cols-${columns.md}` : "",
    columns.lg ? `lg:grid-cols-${columns.lg}` : "",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={`grid ${gridCols} ${gap} ${className}`}>
      {children}
    </div>
  );
}
