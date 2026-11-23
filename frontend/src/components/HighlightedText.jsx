/**
 * מציג text ועוטף ב-<mark> את המופע הראשון של highlight.
 * אם highlight ריק או לא נמצא בטקסט, מוצג הטקסט כמו שהוא.
 * markRef (אופציונלי) מצביע על ה-<mark>, כדי שהקורא יוכל לגלול אליו.
 */
export default function HighlightedText({ text, highlight, markRef }) {
  const start = highlight ? text.indexOf(highlight) : -1;
  if (start === -1) return text;

  const end = start + highlight.length;
  return (
    <>
      {text.slice(0, start)}
      <mark ref={markRef}>{text.slice(start, end)}</mark>
      {text.slice(end)}
    </>
  );
}
