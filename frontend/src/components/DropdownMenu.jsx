import { useEffect, useId, useRef, useState } from "react";

/**
 * תפריט נפתח נגיש (WAI-ARIA menu button).
 *
 * trigger      - התוכן של כפתור הפתיחה (למשל Avatar).
 * label        - שם הכפתור לקורא מסך.
 * header       - תוכן אופציונלי בראש התפריט (למשל האימייל).
 * items        - [{ id, label, onSelect, disabled, badge, separatorBefore }]
 *                disabled + badge: פריט שעוד לא זמין (למשל badge="בקרוב").
 *                separatorBefore: קו מפריד לפני הפריט.
 *
 * מקלדת: חצים למעלה ולמטה, Home ו-End, Escape סוגר. לחיצה מחוץ לתפריט סוגרת.
 */
export default function DropdownMenu({ trigger, label, header, items }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const triggerRef = useRef(null);
  const itemRefs = useRef([]);
  const menuId = useId();

  const enabledIndexes = items.map((item, i) => (item.disabled ? null : i)).filter((i) => i !== null);

  function focusItem(index) {
    itemRefs.current[index]?.focus();
  }

  function close({ returnFocus = false } = {}) {
    setOpen(false);
    if (returnFocus) triggerRef.current?.focus();
  }

  // בפתיחה: פוקוס על הפריט הזמין הראשון. בזמן שפתוח: לחיצה מחוץ לתפריט סוגרת אותו.
  useEffect(() => {
    if (!open) return;
    itemRefs.current.find((el) => el && !el.disabled)?.focus();
    function handlePointerDown(e) {
      if (!rootRef.current?.contains(e.target)) setOpen(false);
    }
    document.addEventListener("pointerdown", handlePointerDown);
    return () => document.removeEventListener("pointerdown", handlePointerDown);
  }, [open]);

  function handleMenuKeyDown(e) {
    const current = enabledIndexes.indexOf(itemRefs.current.indexOf(document.activeElement));
    const last = enabledIndexes.length - 1;
    const moves = {
      ArrowDown: current < last ? current + 1 : 0,
      ArrowUp: current > 0 ? current - 1 : last,
      Home: 0,
      End: last,
    };
    if (e.key in moves) {
      e.preventDefault();
      focusItem(enabledIndexes[moves[e.key]]);
    } else if (e.key === "Escape") {
      e.preventDefault();
      close({ returnFocus: true });
    } else if (e.key === "Tab") {
      close();
    }
  }

  function select(item) {
    close({ returnFocus: true });
    item.onSelect?.();
  }

  return (
    <div className="menu-root" ref={rootRef}>
      <button
        ref={triggerRef}
        type="button"
        className="menu-trigger"
        aria-label={label}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        onClick={() => setOpen((v) => !v)}
      >
        {trigger}
      </button>

      {open && (
        <div className="menu" id={menuId} onKeyDown={handleMenuKeyDown}>
          {header && <div className="menu-header">{header}</div>}
          <ul role="menu" aria-label={label}>
            {items.map((item, i) => (
              <li key={item.id} role="none" className={item.separatorBefore ? "has-separator" : undefined}>
                <button
                  ref={(el) => (itemRefs.current[i] = el)}
                  type="button"
                  role="menuitem"
                  className="menu-item"
                  tabIndex={-1}
                  disabled={item.disabled}
                  onClick={() => select(item)}
                >
                  <span>{item.label}</span>
                  {item.badge && <span className="menu-badge">{item.badge}</span>}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
