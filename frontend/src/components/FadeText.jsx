/**
 * טקסט שנכנס במעבר עדין (fade) בכל פעם שהוא משתנה.
 * key={text} גורם ל-React ליצור את ה-span מחדש כשהטקסט משתנה, וכך האנימציה ב-CSS רצה שוב.
 * האנימציה מוגדרת ב-.fade-in, רק כש-prefers-reduced-motion מאפשר.
 */
export default function FadeText({ text }) {
  return (
    <span key={text} className="fade-in">
      {text}
    </span>
  );
}
