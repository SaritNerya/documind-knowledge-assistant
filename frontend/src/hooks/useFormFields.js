import { useState } from "react";

/**
 * ערכי טופס עם כמה שדות.
 * const { values, bind, setValues, reset } = useFormFields({ email: "", password: "" });
 * <TextField {...bind("email")} />   ← נותן value ו-onChange לשדה
 */
export default function useFormFields(initial) {
  const [values, setValues] = useState(initial);

  const bind = (name) => ({
    value: values[name],
    onChange: (e) => setValues((prev) => ({ ...prev, [name]: e.target.value })),
  });

  return { values, bind, setValues, reset: () => setValues(initial) };
}
