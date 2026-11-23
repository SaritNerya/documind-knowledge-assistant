import { useState } from "react";
import TextField from "./TextField";

function EyeIcon({ crossed }) {
  return (
    <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" focusable="false">
      <path
        d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"
        fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"
      />
      <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="1.8" />
      {crossed && <path d="M4 4l16 16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />}
    </svg>
  );
}

/** שדה סיסמה עם כפתור עין להצגה והסתרה. מקבל את כל ה-props של TextField. */
export default function PasswordField(props) {
  const [visible, setVisible] = useState(false);

  const toggle = (
    <button
      type="button"
      className="field-adornment"
      onClick={() => setVisible((v) => !v)}
      aria-label={visible ? "הסתרת הסיסמה" : "הצגת הסיסמה"}
      aria-pressed={visible}
    >
      <EyeIcon crossed={visible} />
    </button>
  );

  return <TextField {...props} type={visible ? "text" : "password"} adornment={toggle} />;
}
