import { useState } from "react";
import { getToken, clearToken } from "./api";
import Login from "./Login";
import Documents from "./Documents";
import Chat from "./Chat";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(!!getToken());

  if (!loggedIn) return <Login onLogin={() => setLoggedIn(true)} />;

  return (
    <div className="app" dir="rtl">
      <header>
        <h1>DocuMind</h1>
        <button onClick={() => { clearToken(); setLoggedIn(false); }}>התנתקות</button>
      </header>
      <Documents />
      <Chat />
    </div>
  );
}