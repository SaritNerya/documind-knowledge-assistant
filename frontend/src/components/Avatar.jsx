/**
 * עיגול עם האות הראשונה של השם (או של האימייל).
 * דקורטיבי: את השם המלא מציג מי שמשתמש בו (למשל aria-label של הכפתור).
 * האות עטופה ב-span נפרד, כדי שתוכל לקפוץ באנימציה בלי להזיז את העיגול.
 */
export default function Avatar({ name }) {
  const initial = name?.trim().charAt(0).toUpperCase() || "?";
  return (
    <span className="avatar" aria-hidden="true">
      <span className="avatar-letter">{initial}</span>
    </span>
  );
}
