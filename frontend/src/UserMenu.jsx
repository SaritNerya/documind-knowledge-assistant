import { useNavigate } from "react-router-dom";
import { displayNameOf } from "./account/CurrentUserContext";
import Avatar from "./components/Avatar";
import DropdownMenu from "./components/DropdownMenu";
import useCurrentUser from "./hooks/useCurrentUser";

/** תפריט המשתמש בכותרת: עיגול עם האות הראשונה, ותפריט נפתח. */
export default function UserMenu() {
  const { user, logout } = useCurrentUser();
  const navigate = useNavigate();
  const name = displayNameOf(user);

  const items = [
    { id: "profile", label: "פרופיל", onSelect: () => navigate("/profile") },
    { id: "settings", label: "הגדרות", onSelect: () => navigate("/settings") },
    { id: "quota", label: "מכסה יומית", onSelect: () => navigate("/quota") },
    { id: "logout", label: "התנתקות", onSelect: logout, separatorBefore: true },
  ];

  const header = user && (
    <>
      <strong className="menu-header-name">{name}</strong>
      <span className="bidi">{user.email}</span>
    </>
  );

  return (
    <DropdownMenu
      label={name ? `תפריט משתמש: ${name}` : "תפריט משתמש"}
      trigger={<Avatar name={name} />}
      header={header}
      items={items}
    />
  );
}
