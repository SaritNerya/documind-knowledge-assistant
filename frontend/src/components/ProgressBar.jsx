/**
 * פס התקדמות נגיש.
 * value / max: כמה מתוך כמה. label: תיאור לקורא מסך.
 * level: מחרוזת חופשית ל-CSS (למשל "low"), כדי לצבוע את הפס לפי מצב.
 */
export default function ProgressBar({ value, max, label, level }) {
  const percent = max > 0 ? Math.min(100, Math.max(0, (value / max) * 100)) : 0;
  return (
    <div
      className="progress"
      data-level={level}
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={value}
    >
      <span className="progress-fill" style={{ width: `${percent}%` }} />
    </div>
  );
}
