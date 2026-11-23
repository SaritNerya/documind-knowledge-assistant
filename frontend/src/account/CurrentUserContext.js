import { createContext } from "react";

/**
 * המשתמשת המחוברת, משותפת לכל האפליקציה (תפריט, פרופיל, הגדרות).
 * user: { id, email, display_name, created_at } או null עד שנטען.
 * setUser: מעדכן אחרי שינוי (למשל שם תצוגה), וכך האווטאר מתעדכן מיד.
 * logout: התנתקות ומעבר למסך הכניסה.
 */
export const CurrentUserContext = createContext({ user: null, setUser: () => {}, logout: () => {} });

/** השם שמוצג: שם התצוגה, ואם אין, החלק שלפני ה-@ באימייל. */
export function displayNameOf(user) {
  return user?.display_name || user?.email.split("@")[0] || "";
}
