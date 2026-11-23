import { useState } from "react";
import { updateProfile } from "../api";
import StatusMessage from "../components/StatusMessage";
import TextField from "../components/TextField";
import useAsyncAction from "../hooks/useAsyncAction";
import useCurrentUser from "../hooks/useCurrentUser";
import { displayNameOf } from "./CurrentUserContext";

const DISPLAY_NAME_MAX_LENGTH = 50; // תואם ל-DISPLAY_NAME_MAX_LENGTH בשרת

/** עריכת שם התצוגה. אחרי שמירה המשתמשת מתעדכנת בכל האתר (גם האות באווטאר). */
export default function DisplayNameForm() {
  const { user, setUser } = useCurrentUser();
  const [name, setName] = useState(user.display_name ?? "");
  const save = useAsyncAction();
  const changed = name.trim() !== (user.display_name ?? "");

  async function handleSubmit(e) {
    e.preventDefault();
    await save.run(async () => setUser(await updateProfile(name)), "השם נשמר");
  }

  return (
    <form className="inline-form" onSubmit={handleSubmit}>
      <TextField
        label="שם תצוגה"
        value={name}
        onChange={(e) => setName(e.target.value)}
        maxLength={DISPLAY_NAME_MAX_LENGTH}
        placeholder={displayNameOf({ email: user.email })}
        hint="כך תופיעי באתר. השארת השדה ריק תציג את תחילת האימייל."
      />
      <button type="submit" className="btn-playful" disabled={!changed || save.pending}>
        {save.pending ? "שומרת..." : "שמירה"}
      </button>
      <StatusMessage tone={save.tone} message={save.message} />
    </form>
  );
}
