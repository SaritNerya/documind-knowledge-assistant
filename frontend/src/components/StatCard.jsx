/** כרטיס מספר קטן: ערך גדול ותווית מתחתיו (למשל "12 / מסמכים"). */
export default function StatCard({ value, label, icon }) {
  return (
    <div className="stat-card">
      {icon && <span className="stat-icon" aria-hidden="true">{icon}</span>}
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}
