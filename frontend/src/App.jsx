import { useState } from "react";
import { Link, Navigate, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import { clearToken, getToken } from "./api";
import CurrentUserProvider from "./account/CurrentUserProvider";
import ProfilePage from "./account/ProfilePage";
import QuotaPage from "./account/QuotaPage";
import SettingsPage from "./account/SettingsPage";
import ChatPage from "./ChatPage";
import Logo from "./components/Logo";
import Login from "./Login";
import UserMenu from "./UserMenu";

/** המסגרת של משתמשת מחוברת: כותרת עם לוגו ותפריט משתמש, ומתחתיה העמוד הנוכחי. */
function Workspace({ onLogout }) {
  return (
    <CurrentUserProvider onLogout={onLogout}>
      <div className="app" dir="rtl">
        <header>
          <h1 className="site-title">
            {/* לחיצה על הלוגו פותחת שיחה חדשה */}
            <Link to="/new" className="logo-link" aria-label="DocuMind, שיחה חדשה" title="שיחה חדשה">
              <Logo />
            </Link>
          </h1>
          <UserMenu />
        </header>
        <Outlet />
      </div>
    </CurrentUserProvider>
  );
}

export default function App() {
  const [loggedIn, setLoggedIn] = useState(!!getToken());
  const navigate = useNavigate();

  function handleLogin() {
    setLoggedIn(true);
    navigate("/", { replace: true });
  }

  function handleLogout() {
    clearToken();
    setLoggedIn(false);
    navigate("/login", { replace: true });
  }

  return (
    <Routes>
      <Route
        path="/login"
        element={loggedIn ? <Navigate to="/" replace /> : <Login onLogin={handleLogin} />}
      />
      <Route
        element={
          loggedIn ? <Workspace onLogout={handleLogout} /> : <Navigate to="/login" replace />
        }
      >
        {/* כל הכתובות של הצ'אט חולקות רכיב אחד, כדי שהמצב לא יתאפס במעבר בין שיחות.
            ChatPage קורא את הכתובת בעצמו (useMatch), ולכן לנתיבים הפנימיים אין element. */}
        <Route element={<ChatPage />}>
          <Route index />
          <Route path="new" />
          <Route path="c/:conversationId" />
        </Route>

        {/* עמודי החשבון, מתפריט המשתמש */}
        <Route path="profile" element={<ProfilePage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="quota" element={<QuotaPage />} />
      </Route>
      <Route path="*" element={<Navigate to={loggedIn ? "/" : "/login"} replace />} />
    </Routes>
  );
}
