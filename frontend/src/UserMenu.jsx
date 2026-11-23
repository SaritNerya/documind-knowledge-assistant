import Avatar from "./components/Avatar";
import DropdownMenu from "./components/DropdownMenu";
import useCurrentUser from "./hooks/useCurrentUser";

// פריט שעוד לא מומש: מוצג בתפריט, אבל לא לחיץ
const COMING_SOON = { disabled: true, badge: "בקרוב" };

/** תפריט המשתמש בכותרת: עיגול עם האות הראשונה, ותפריט נפתח. */
export default function UserMenu({ onLogout }) {
  const user = useCurrentUser();
  const email = user?.email ?? "";

  // כדי לממש פריט: להחליף את COMING_SOON ב-onSelect: () => ...
  const items = [
    { id: "profile", label: "פרופיל", ...COMING_SOON },
    { id: "settings", label: "הגדרות", ...COMING_SOON },
    { id: "quota", label: "מכסה יומית", ...COMING_SOON },
    { id: "logout", label: "התנתקות", onSelect: onLogout, separatorBefore: true },
  ];

  return (
    <DropdownMenu
      label={email ? `תפריט משתמש: ${email}` : "תפריט משתמש"}
      trigger={<Avatar name={email} />}
      header={email && <span className="bidi">{email}</span>}
      items={items}
    />
  );
}
