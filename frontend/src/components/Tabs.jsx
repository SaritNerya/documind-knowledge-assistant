/**
 * לשוניות נגישות (WAI-ARIA tabs).
 * tabs: [{ id, label }], value: הלשונית הפעילה, onChange(id).
 * panelId: ה-id של הפאנל שהלשוניות שולטות בו. מזהה כל לשונית הוא `${panelId}-${tab.id}`,
 * כך שהפאנל יכול להצביע עליה ב-aria-labelledby.
 * מקלדת: חצים (מותאם לכיוון RTL), Home ו-End.
 */
export default function Tabs({ tabs, value, onChange, panelId, label }) {
  function handleKeyDown(e) {
    const index = tabs.findIndex((t) => t.id === value);
    const rtl = getComputedStyle(e.currentTarget).direction === "rtl";
    const step = { ArrowLeft: rtl ? 1 : -1, ArrowRight: rtl ? -1 : 1 }[e.key];
    let next = null;
    if (step) next = (index + step + tabs.length) % tabs.length;
    if (e.key === "Home") next = 0;
    if (e.key === "End") next = tabs.length - 1;
    if (next === null) return;
    e.preventDefault();
    onChange(tabs[next].id);
    document.getElementById(`${panelId}-${tabs[next].id}`)?.focus();
  }

  return (
    <div className="tabs" role="tablist" aria-label={label} onKeyDown={handleKeyDown}>
      {tabs.map((tab) => {
        const selected = tab.id === value;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            id={`${panelId}-${tab.id}`}
            className={`tab${selected ? " is-selected" : ""}`}
            aria-selected={selected}
            aria-controls={panelId}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(tab.id)}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
