import { useEffect, useState } from "react";
import { getCurrentUser } from "../api";

/** המשתמש המחובר ({ id, email }), או null עד שהוא נטען. */
export default function useCurrentUser() {
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

  return user;
}
