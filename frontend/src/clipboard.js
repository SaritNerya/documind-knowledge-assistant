/**
 * מעתיק טקסט ללוח. מחזיר Promise שמצליח או נכשל.
 *
 * navigator.clipboard עובד רק בדף מאובטח (https, או localhost בפיתוח).
 * בדף http רגיל הוא לא קיים, ואז משתמשים בדרך הישנה: textarea זמני ו-execCommand("copy").
 */
export async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text);
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed"; // לא גורם לגלילה של הדף
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  try {
    if (!document.execCommand("copy")) throw new Error("copy failed");
  } finally {
    textarea.remove();
  }
}
