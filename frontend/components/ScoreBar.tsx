"use client";

interface ScoreBarProps {
  /** Human-readable label for the score */
  label: string;
  /** Score value between 0 and 10 */
  value: number;
  /** Tailwind background color class for the filled bar, e.g. "bg-blue-500" */
  color?: string;
}

/**
 * Renders a labelled horizontal progress bar representing a score out of 10.
 */
export default function ScoreBar({
  label,
  value,
  color = "bg-primary-600",
}: ScoreBarProps) {
  const pct = Math.min(Math.max((value / 10) * 100, 0), 100);
  const displayValue = value.toFixed(1);

  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-600 w-36 shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-2.5 overflow-hidden">
        <div
          className={`${color} h-2.5 rounded-full transition-all duration-500`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={10}
        />
      </div>
      <span className="text-sm font-semibold text-primary-700 w-8 text-right">
        {displayValue}
      </span>
    </div>
  );
}
