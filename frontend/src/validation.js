// בדיקות תקינות של טפסים. פונקציות טהורות, בלי React, כדי שיהיה קל לקרוא ולבדוק אותן.

export const PASSWORD_MIN_LENGTH = 8; // תואם ל-UserCreate בשרת

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// בכל הפונקציות: שגיאות רק לשדות שכבר הוקלד בהם משהו. שדה ריק לא מקבל שגיאה,
// כדי לא "לצעוק" על טופס חדש.

/** כללי סיסמה חדשה ואימות שלה. משותף להרשמה ולהחלפת סיסמה. */
function newPasswordErrors(password, confirm) {
  const errors = {};
  if (password && password.length < PASSWORD_MIN_LENGTH) {
    errors.password = `הסיסמה קצרה מדי (לפחות ${PASSWORD_MIN_LENGTH} תווים)`;
  }
  if (confirm && confirm !== password) {
    errors.confirm = "הסיסמאות לא תואמות";
  }
  return errors;
}

export function validateAuthForm({ email, password, confirm }, isRegister) {
  const errors = isRegister ? newPasswordErrors(password, confirm) : {};
  if (email && !EMAIL_PATTERN.test(email.trim())) {
    errors.email = "האימייל לא תקין";
  }
  return errors;
}

export function validatePasswordChange({ current, password, confirm }) {
  const errors = newPasswordErrors(password, confirm);
  if (!errors.password && current && password && current === password) {
    errors.password = "הסיסמה החדשה זהה לנוכחית";
  }
  return errors;
}

const STRENGTH_LABELS = ["חלשה מאוד", "חלשה", "בינונית", "טובה", "חזקה"];
const CHARACTER_CLASSES = [/[a-zא-ת]/, /[A-Z]/, /\d/, /[^\p{L}\d\s]/u];

/** ציון 0 עד 4: נקודה על אורך מינימלי, על 12 תווים ומעלה, ועל גיוון (2 ו-3 סוגי תווים). */
export function passwordStrength(password) {
  if (!password) return { score: 0, label: "" };
  const variety = CHARACTER_CLASSES.filter((pattern) => pattern.test(password)).length;
  const longEnough = password.length >= PASSWORD_MIN_LENGTH;
  let score = [longEnough, password.length >= 12, variety >= 2, variety >= 3].filter(Boolean).length;
  if (!longEnough) score = Math.min(score, 1); // סיסמה קצרה לא יכולה להיות "טובה"
  return { score, label: STRENGTH_LABELS[score] };
}
