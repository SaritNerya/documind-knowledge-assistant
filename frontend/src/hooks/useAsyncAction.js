import { useState } from "react";

const IDLE = { pending: false, tone: null, message: "" };

/**
 * מריץ פעולה אסינכרונית (שמירה, מחיקה...) ומנהל עבורה מצב טעינה והודעה.
 *
 * const { run, pending, tone, message } = useAsyncAction();
 * const ok = await run(() => updateProfile(name), "נשמר");
 *
 * tone: "success" | "error" | null. run מחזיר true אם הפעולה הצליחה.
 */
export default function useAsyncAction() {
  const [state, setState] = useState(IDLE);

  async function run(action, successMessage = "") {
    setState({ ...IDLE, pending: true });
    try {
      await action();
      setState({ ...IDLE, tone: "success", message: successMessage });
      return true;
    } catch (err) {
      setState({ ...IDLE, tone: "error", message: err.message });
      return false;
    }
  }

  return { ...state, run, reset: () => setState(IDLE) };
}
