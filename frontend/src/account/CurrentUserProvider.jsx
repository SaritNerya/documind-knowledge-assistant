import { useEffect, useState } from "react";
import { getCurrentUser } from "../api";
import { CurrentUserContext } from "./CurrentUserContext";

/** טוען את המשתמשת המחוברת פעם אחת ומשתף אותה דרך CurrentUserContext. */
export default function CurrentUserProvider({ onLogout, children }) {
  const [user, setUser] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getCurrentUser()
      .then((data) => !cancelled && setUser(data))
      .catch(() => {}); // 401 כבר מטופל ב-api.js (מעבר למסך הכניסה); בשאר המקרים נשאר null
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <CurrentUserContext.Provider value={{ user, setUser, logout: onLogout }}>
      {children}
    </CurrentUserContext.Provider>
  );
}
