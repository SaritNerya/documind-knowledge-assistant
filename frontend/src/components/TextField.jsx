import { useId } from "react";

/**
 * שדה טקסט עם תווית, הודעת שגיאה או רמז, ותוספות אופציונליות:
 * adornment - כפתור בתוך השדה (למשל עין להצגת סיסמה)
 * children - תוכן מתחת לשדה (למשל מד חוזק)
 * כל שאר ה-props עוברים ל-input עצמו.
 */
export default function TextField({ label, error, hint, adornment, children, ...inputProps }) {
  const id = useId();
  const messageId = `${id}-message`;
  const message = error || hint;

  return (
    <div className={`field${error ? " has-error" : ""}${adornment ? " has-adornment" : ""}`}>
      <label htmlFor={id}>{label}</label>
      <div className="field-control">
        <input
          id={id}
          aria-invalid={error ? true : undefined}
          aria-describedby={message ? messageId : undefined}
          {...inputProps}
        />
        {adornment}
      </div>
      {children}
      {message && (
        <p id={messageId} className={error ? "field-error" : "field-hint"} aria-live="polite">
          {message}
        </p>
      )}
    </div>
  );
}
