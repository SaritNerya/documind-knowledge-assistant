import { useState } from "react";
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { getToken, clearToken } from "./api";
import Login from "./Login";
import Documents from "./Documents";
import Chat from "./Chat";

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
        path="/"
        element={
          loggedIn ? (
            <div className="app" dir="rtl">
              <header>
                <h1>DocuMind</h1>
                <button onClick={handleLogout}>התנתקות</button>
              </header>
              <Documents />
              <Chat />
            </div>
          ) : (
            <Navigate to="/login" replace />
          )
        }
      />
      <Route path="*" element={<Navigate to={loggedIn ? "/" : "/login"} replace />} />
    </Routes>
  );
}