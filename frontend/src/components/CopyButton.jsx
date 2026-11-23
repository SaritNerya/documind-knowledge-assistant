import { useEffect, useRef, useState } from "react";
import { copyText } from "../clipboard";

const FEEDBACK_MS = 2000; // כמה זמן מוצג "הועתק" לפני שהכפתור חוזר למצבו הרגיל

function CopyIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <rect x="9" y="9" width="11" height="11" rx="2" />
      <path d="M5 15V5a2 2 0 0 1 2-2h10" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M5 12.5 10 17 19 7" />
    </svg>
  );
}

/**
 * כפתור אייקון קטן שמעתיק טקסט ללוח, ומראה וי לשתי שניות אחרי הצלחה.
 * text  - הטקסט להעתקה.
 * label - התיאור לקורא מסך ולטולטיפ (למשל "העתקת התשובה").
 */
export default function CopyButton({ text, label = "העתקה" }) {
  const [status, setStatus] = useState("idle"); // "idle" | "copied" | "failed"
  const timer = useRef(null);

  // ניקוי הטיימר אם הרכיב נעלם לפני שעברו שתי השניות
  useEffect(() => () => clearTimeout(timer.current), []);

  async function handleClick() {
    try {
      await copyText(text);
      setStatus("copied");
    } catch {
      setStatus("failed");
    }
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setStatus("idle"), FEEDBACK_MS);
  }

  const message = { copied: "הועתק", failed: "ההעתקה נכשלה" }[status];

  return (
    <button
      type="button"
      className={`icon-button copy-button is-${status}`}
      onClick={handleClick}
      aria-label={label}
      title={message ?? label}
    >
      {status === "copied" ? <CheckIcon /> : <CopyIcon />}
      {/* הודעה לקורא מסך, ומופיעה גם לעין ליד האייקון */}
      <span className="copy-status" aria-live="polite">{message}</span>
    </button>
  );
}
