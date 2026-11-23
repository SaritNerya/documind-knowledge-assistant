/** הלוגו: ספר פתוח עם עלה, ולצידו השם. הצבעים מגיעים מהטוקנים דרך CSS. */
export default function Logo({ as: Heading = "span" }) {
  return (
    <Heading className="logo">
      <svg className="logo-mark" viewBox="0 0 48 48" aria-hidden="true" focusable="false">
        <path className="logo-page" d="M24 14c-5-4-12-4-18-2v24c6-2 13-2 18 2 5-4 12-4 18-2V12c-6-2-13-2-18 2Z" />
        <path className="logo-spine" d="M24 14v24" />
        <path className="logo-leaf" d="M30 9c6 0 10 3 11 8-6 1-11-2-11-8Z" />
      </svg>
      <span className="logo-name">DocuMind</span>
    </Heading>
  );
}
