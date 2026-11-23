import { useRef, useState } from "react";

/** האם הקובץ מתאים ל-accept (רשימת סיומות כמו ".pdf,.docx"). accept ריק מקבל הכול. */
function matchesAccept(file, accept) {
  if (!accept) return true;
  const name = file.name.toLowerCase();
  return accept.split(",").some((ext) => name.endsWith(ext.trim().toLowerCase()));
}

/**
 * אזור העלאת קובץ: גרירה ושחרור, או לחיצה לבחירה מהמחשב.
 *
 * accept   - סיומות מותרות, כמו ב-<input type="file">. חל גם על קובץ שנגרר.
 * onFile   - נקרא עם קובץ אחד תקין.
 * onReject - נקרא עם הודעה כשהקובץ שנגרר לא מתאים ל-accept.
 * children - הטקסט שבתוך האזור.
 *
 * האזור הוא <label> שעוטף input מוסתר, ולכן גם מקלדת וקורא מסך עובדים כמו בכפתור קבצים רגיל.
 */
export default function FileDropZone({ accept, disabled = false, onFile, onReject, children }) {
  const [dragging, setDragging] = useState(false);
  // dragenter/dragleave נורים גם על אלמנטים פנימיים. סופרים כניסות ויציאות כדי שההדגשה לא תהבהב.
  const depth = useRef(0);

  function handleFiles(files) {
    const file = files?.[0];
    if (!file) return;
    if (matchesAccept(file, accept)) onFile(file);
    else onReject?.(`אפשר להעלות רק קבצים מסוג ${accept}`);
  }

  function handleDragEnter(e) {
    e.preventDefault();
    if (disabled) return;
    depth.current += 1;
    setDragging(true);
  }

  function handleDragLeave(e) {
    e.preventDefault();
    depth.current = Math.max(0, depth.current - 1);
    if (depth.current === 0) setDragging(false);
  }

  function handleDrop(e) {
    e.preventDefault(); // בלי זה הדפדפן פותח את הקובץ בלשונית
    depth.current = 0;
    setDragging(false);
    if (!disabled) handleFiles(e.dataTransfer.files);
  }

  function handleChange(e) {
    handleFiles(e.target.files);
    e.target.value = ""; // מאפשר לבחור שוב את אותו קובץ
  }

  const className = ["dropzone", dragging && "is-dragging", disabled && "is-disabled"]
    .filter(Boolean)
    .join(" ");

  return (
    <label
      className={className}
      onDragEnter={handleDragEnter}
      onDragOver={(e) => e.preventDefault()} // חובה כדי שהדפדפן יאפשר drop
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input
        type="file"
        className="visually-hidden"
        accept={accept}
        disabled={disabled}
        onChange={handleChange}
      />
      {children}
    </label>
  );
}
