import { useContext } from "react";
import { CurrentUserContext } from "../account/CurrentUserContext";

/** { user, setUser, logout } של המשתמשת המחוברת. חייב לרוץ בתוך CurrentUserProvider. */
export default function useCurrentUser() {
  return useContext(CurrentUserContext);
}
