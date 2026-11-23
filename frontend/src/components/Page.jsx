import { Link } from "react-router-dom";

/**
 * שלד לעמוד תוכן (פרופיל, הגדרות...): קישור חזרה לצ'אט, כותרת, תת-כותרת ותוכן.
 * העמוד גולל בעצמו, כמו אזור ההודעות בצ'אט.
 */
export default function Page({ title, subtitle, children }) {
  return (
    <main className="page">
      <div className="page-inner">
        <Link to="/" className="page-back">→ חזרה לשיחות</Link>
        <h2 className="page-title">{title}</h2>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
        {children}
      </div>
    </main>
  );
}
