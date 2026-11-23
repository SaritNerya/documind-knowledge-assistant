/**
 * הודעת מצב קצרה אחרי פעולה: הצלחה (ירוק, עם וי) או שגיאה (אדום).
 * key={message} מריץ מחדש את אנימציית ה"קפיצה" בכל הודעה חדשה.
 */
export default function StatusMessage({ tone, message }) {
  if (!tone || !message) return null;
  return (
    <p key={message} className={`status-message is-${tone}`} role={tone === "error" ? "alert" : "status"}>
      {tone === "success" && <span aria-hidden="true">✓ </span>}
      {message}
    </p>
  );
}
