// הודעות שגיאה ברורות למשתמשת, בעברית.
// השרת שולח חלק מההודעות באנגלית (מיועדות למפתחים), וכאן הן מתורגמות.
// הודעות שהשרת כבר שולח בעברית עוברות כמו שהן.

/** כשהבקשה לא הגיעה לשרת בכלל (בדפדפן: "Failed to fetch") */
export const NETWORK_ERROR = "אין חיבור לשרת. בדקי את החיבור לאינטרנט ונסי שוב בעוד רגע.";

const HEBREW = /[֐-׿]/;

// הודעות השרת באנגלית ← עברית. הסדר חשוב: הודעה ספציפית לפני הודעה כללית שמתחילה כמוה.
const SERVER_MESSAGES = [
  [/^Incorrect email or password/, "האימייל או הסיסמה שגויים"],
  [/^Email already registered/, "כבר קיים חשבון עם האימייל הזה"],
  [/^Invalid invitation code/, "קוד ההזמנה שגוי"],
  [/^Could not validate credentials/, "פג תוקף ההתחברות. צריך להתחבר מחדש."],
  [/^Only PDF and DOCX/, "אפשר להעלות רק קבצי PDF או Word (DOCX)"],
  [/^File too large \(max (\d+) MB\)/, (match) => `הקובץ גדול מדי. אפשר להעלות עד ${match[1]}MB.`],
  [/^A document with this name already exists/, "כבר יש בשיחה הזו מסמך באותו שם"],
  [/^Document limit reached for this conversation/, "הגעת למספר המסמכים המקסימלי בשיחה הזו"],
  [/^Document limit reached/, "הגעת למספר המסמכים המקסימלי בחשבון"],
  [/^No text found in the file/, "לא נמצא טקסט בקובץ. אולי זו סריקה של תמונה?"],
  [/^Could not read the file/, "לא הצלחתי לקרוא את הקובץ. ייתכן שהוא פגום, מוגן בסיסמה או ארוך מדי."],
  [/^Embedding service unavailable/, "שירות עיבוד המסמכים לא זמין כרגע. נסי שוב בעוד רגע."],
  [/^LLM service unavailable/, "שירות התשובות לא זמין כרגע. נסי שוב בעוד רגע."],
  [/^Conversation not found/, "השיחה לא נמצאה"],
  [/^Document not found/, "המסמך לא נמצא"],
];

// כשאין הודעה מוכרת: הודעה כללית לפי סוג השגיאה
const BY_STATUS = {
  400: "הבקשה לא תקינה",
  401: "צריך להתחבר מחדש",
  403: "אין לך הרשאה לפעולה הזו",
  404: "לא נמצא",
  409: "הפריט כבר קיים",
  413: "הקובץ גדול מדי",
  422: "הנתונים שהוזנו אינם תקינים",
  429: "יותר מדי בקשות. נסי שוב בעוד רגע.",
};
const SERVER_ERROR = "משהו השתבש בשרת. נסי שוב בעוד רגע.";
const UNKNOWN_ERROR = "משהו השתבש. נסי שוב.";

/** הודעה ברורה לשגיאה מהשרת. detail: השדה detail מהתשובה (מחרוזת, רשימה או undefined). */
export function friendlyError(status, detail) {
  if (typeof detail === "string") {
    if (HEBREW.test(detail)) return detail;
    for (const [pattern, message] of SERVER_MESSAGES) {
      const match = detail.match(pattern);
      if (match) return typeof message === "function" ? message(match) : message;
    }
  }
  if (status >= 500) return SERVER_ERROR;
  return BY_STATUS[status] ?? UNKNOWN_ERROR;
}
