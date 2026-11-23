import { passwordStrength } from "../validation";

const SEGMENTS = 4;

/** פס צבעוני של חוזק סיסמה. הצבע לכל רמה נקבע ב-CSS לפי data-level. */
export default function PasswordStrength({ password }) {
  if (!password) return null;
  const { score, label } = passwordStrength(password);

  return (
    <div
      className="strength"
      data-level={score}
      role="meter"
      aria-label="חוזק הסיסמה"
      aria-valuemin={0}
      aria-valuemax={SEGMENTS}
      aria-valuenow={score}
      aria-valuetext={label}
    >
      <div className="strength-bar" aria-hidden="true">
        {Array.from({ length: SEGMENTS }, (_, i) => (
          <span key={i} className={i < score ? "is-filled" : undefined} />
        ))}
      </div>
      <span className="strength-label">{label}</span>
    </div>
  );
}
