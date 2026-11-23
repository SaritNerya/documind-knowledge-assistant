import { useEffect, useState } from "react";

/**
 * טוען נתונים מהשרת פעם אחת, כשהרכיב עולה.
 * load: פונקציה שמחזירה Promise (למשל getUsage).
 * מחזיר { data, error, loading }.
 */
export default function useApiData(load) {
  const [state, setState] = useState({ data: null, error: "", loading: true });

  useEffect(() => {
    let cancelled = false;
    load()
      .then((data) => !cancelled && setState({ data, error: "", loading: false }))
      .catch((err) => !cancelled && setState({ data: null, error: err.message, loading: false }));
    return () => {
      cancelled = true;
    };
  }, [load]);

  return state;
}
