import { useState } from "react";
import { deleteAccount } from "../api";
import StatusMessage from "../components/StatusMessage";
import TextField from "../components/TextField";
import useAsyncAction from "../hooks/useAsyncAction";
import useCurrentUser from "../hooks/useCurrentUser";

/**
 * מחיקת חשבון, עם אישור כפול כי המשתמשות מעלות מסמכים אישיים:
 * 1. לחיצה על "אני רוצה למחוק" פותחת את שלב האישור.
 * 2. כפתור המחיקה נפתח רק אחרי הקלדת האימייל המדויק. השרת בודק את האימייל שוב.
 */
export default function DeleteAccountSection() {
  const { user, logout } = useCurrentUser();
  const [confirming, setConfirming] = useState(false);
  const [typedEmail, setTypedEmail] = useState("");
  const removal = useAsyncAction();
  const emailMatches = typedEmail.trim().toLowerCase() === user.email.toLowerCase();

  function cancel() {
    setConfirming(false);
    setTypedEmail("");
    removal.reset();
  }

  async function handleDelete(e) {
    e.preventDefault();
    if (!emailMatches) return;
    if (await removal.run(() => deleteAccount(typedEmail))) logout();
  }

  return (
    <section className="card page-section danger-zone">
      <h3>מחיקת חשבון</h3>
      <p>
        המחיקה מסירה לצמיתות את כל השיחות, ההודעות והמסמכים שהעלית. <strong>אי אפשר לבטל אותה.</strong>
      </p>

      {!confirming ? (
        <button type="button" className="btn-danger-outline btn-playful" onClick={() => setConfirming(true)}>
          אני רוצה למחוק את החשבון
        </button>
      ) : (
        <form onSubmit={handleDelete}>
          <TextField
            label="כדי לאשר, הקלידי את האימייל שלך:"
            hint={user.email}
            type="email"
            dir="ltr"
            autoComplete="off"
            autoFocus
            value={typedEmail}
            onChange={(e) => setTypedEmail(e.target.value)}
          />
          <div className="button-row">
            <button type="submit" className="btn-danger btn-playful" disabled={!emailMatches || removal.pending}>
              {removal.pending ? "מוחקת..." : "מחיקה לצמיתות"}
            </button>
            <button type="button" className="btn-ghost" onClick={cancel}>ביטול</button>
          </div>
          <StatusMessage tone={removal.tone} message={removal.message} />
        </form>
      )}
    </section>
  );
}
