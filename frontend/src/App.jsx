import { useState } from "react";
import { Link, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { getToken, clearToken } from "./api";
import Login from "./Login";
import Logo from "./components/Logo";
import ChatPage from "./ChatPage";

function Workspace({ onLogout }) {
  return (
    <div className="app" dir="rtl">
      <header>
        <h1 className="site-title">
          {/* לחיצה על הלוגו פותחת שיחה חדשה */}
          <Link to="/new" className="logo-link" aria-label="DocuMind, שיחה חדשה" title="שיחה חדשה">
            <Logo />
          </Link>
        </h1>
        <button type="button" className="btn-ghost" onClick={onLogout}>התנתקות</button>
      </header>
      <ChatPage />
    </div>
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
      {/* כל הכתובות של הצ'אט חולקות רכיב אחד, כדי שהמצב לא יתאפס במעבר בין שיחות.
          ChatPage קורא את הכתובת בעצמו (useMatch), ולכן לנתיבים הפנימיים אין element. */}
      <Route
        element={
          loggedIn ? <Workspace onLogout={handleLogout} /> : <Navigate to="/login" replace />
        }
      >
        <Route index />
        <Route path="new" />
        <Route path="c/:conversationId" />
      </Route>
      <Route path="*" element={<Navigate to={loggedIn ? "/" : "/login"} replace />} />
    </Routes>
  );
}
