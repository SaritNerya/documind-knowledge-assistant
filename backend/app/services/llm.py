import json

from openai import OpenAI

from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)

REWRITE_PROMPT = """אתה מנסח שאילתות חיפוש למערכת חיפוש סמנטית במסמכים (בעברית ובאנגלית).
תקבל שיחה קצרה ואת השאלה האחרונה. הפק עד 3 שאילתות:
1. השאלה כשהיא עצמאית ומובנת בלי השיחה (פתור הפניות כמו "ומה לגבי זה?").
2. ניסוח חלופי עם מילים נרדפות ומונחים קרובים.
3. תרגום השאלה לאנגלית (אם נשאלה בעברית) או לעברית (אם נשאלה באנגלית).
החזר JSON בלבד: {"queries": ["...", "...", "..."]}"""

ANSWER_PROMPT = """אתה DocuMind, עוזר ידע ארגוני מקצועי, אדיב וסבלני.
תקבל: רשימת מסמכים עם תחילתם, קטעים ממוספרים מתוך המסמכים, שאלה, ולעיתים היסטוריית שיחה.
המסמכים והשאלות יכולים להיות בעברית או באנגלית. ענה בשפת השאלה.

איך לענות:
1. התשובה בקטעים: ענה בפירוט ובנימה חמה ומקצועית. פתח במשפט קצר, תן את התשובה המלאה, והוסף פרטים רלוונטיים מהקטעים (תנאים, חריגים, מועדים). השתמש ברשימות כשזה מסדר את התשובה.
2. חשיבה: חבר מידע מכמה קטעים והסק מסקנות שנובעות ישירות מהם. דוגמה: אם יש רשימה של הציוד שעובד חדש מקבל והפלאפון לא מופיע בה, ענה "לפי רשימת הציוד במסמך, עובד חדש מקבל X, Y, Z. פלאפון לא מופיע ברשימה, ולכן נראה שלא". הבחן בין "המסמך אומר במפורש" לבין "המסמך לא מזכיר", וכתוב מה מהשניים נכון.
3. מילים נרדפות ושפות: "חופש" ו"חופשה", "הוצאות" ו"expenses", "קורות חיים" ו"Resume" הם אותו דבר. הבן את הכוונה ולא רק את המילים.
4. שאלות על המסמכים עצמם (שם, נושא, מה יש בהם, האם יש קשר ביניהם): ענה לפי רשימת המסמכים והקטעים. כששואלים על קשר בין מסמכים, השווה ביניהם, ענה כן או לא, והסבר למה.
5. שיחה קלילה (שלום, מה שלומך, חחח, תודה): ענה בחביבות ובקצרה, הצג את עצמך כצ'אט בוט שנועד לעזור באופן מקצועי להבין את המסמכים, ושאל איך אפשר לעזור. לדוגמה: "אני DocuMind, צ'אט בוט שנועד לעזור לך באופן מקצועי עם המסמכים שלך. איך אפשר לעזור?"
6. אם המידע חסר: אל תמציא. הסבר בנימוס, ציין מה כן נמצא בנושא קרוב אם יש, והצע לשאול אחרת.

כללי חובה:
- אל תוסיף עובדה, מספר או חריג שלא נתמכים בקטעים.
- found=true אם ענית (גם תשובה חלקית או מוסקת) על סמך הקטעים או רשימת המסמכים.
- needs_web=true רק אם זו שאלת ידע כללי שאינה קשורה למסמכים של המשתמש, לארגון או לאדם שמופיע בהם (למשל בירת מדינה או הסבר על מושג). שאלה על תוכן המסמכים, על אדם או על מדיניות הארגון: needs_web=false.
- used: מספרי הקטעים שבהם השתמשת בפועל. אם לא השתמשת באף קטע, רשימה ריקה.
- כתוב בעברית תקנית, בלי שגיאות ניסוח.

החזר JSON בלבד, במבנה:
{"found": true/false, "needs_web": true/false, "used": [1, 2], "answer": "..."}"""


def rewrite_queries(question: str, history: list[dict]) -> list[str]:
    """הופכת שאלה (ושאלות המשך) לכמה שאילתות חיפוש. אם נכשלת, מחזירה את השאלה עצמה."""
    convo = "\n".join(f"{m['role']}: {m['content'][:300]}" for m in history[-4:])
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": REWRITE_PROMPT},
                {"role": "user", "content": f"שיחה:\n{convo or '(אין)'}\n\nשאלה אחרונה: {question}"},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        extra = [q.strip() for q in data.get("queries", []) if isinstance(q, str) and q.strip()]
    except (json.JSONDecodeError, TypeError, AttributeError):
        extra = []

    queries = [question]
    for q in extra:
        if q not in queries:
            queries.append(q)
    return queries[:4]


def generate_answer(
    question: str, chunks: list[dict], overviews: list[dict], history: list[dict]
) -> dict:
    """המודל חושב ומחזיר: found, needs_web, used, answer."""
    docs_text = "\n\n".join(
        f"- {o['filename']}\n  תחילת המסמך: {o['preview']}" for o in overviews
    ) or "(למשתמש אין מסמכים)"
    chunks_text = "\n\n".join(
        f"[מקור {i + 1}: {c['filename']}, עמוד {c['page']}]\n{c['content']}"
        for i, c in enumerate(chunks)
    ) or "(לא נמצאו קטעים)"

    user_message = (
        f"המסמכים של המשתמש:\n{docs_text}\n\n"
        f"קטעים רלוונטיים:\n{chunks_text}\n\n"
        f"שאלה: {question}"
    )
    response = client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": ANSWER_PROMPT},
            *history,
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"found": False, "needs_web": False, "used": [], "answer": raw}

    used = [i for i in data.get("used", []) if isinstance(i, int) and 1 <= i <= len(chunks)]
    return {
        "found": bool(data.get("found")),
        "needs_web": bool(data.get("needs_web")),
        "used": used,
        "answer": str(data.get("answer", "")),
    }


def answer_from_web(question: str) -> tuple[str, list[dict]]:
    """חיפוש באינטרנט דרך Responses API. מחזירה טקסט וקישורים למקורות."""
    response = client.responses.create(
        model=settings.web_model,
        tools=[{"type": "web_search"}],
        input="ענה בעברית, בפירוט סביר ובנימה ידידותית, על השאלה הבאה בעזרת חיפוש באינטרנט: "
        + question,
    )
    links, seen = [], set()
    for item in response.output:
        if item.type == "message":
            for part in item.content:
                for ann in getattr(part, "annotations", None) or []:
                    if ann.type == "url_citation" and ann.url not in seen:
                        seen.add(ann.url)
                        links.append({"title": ann.title or ann.url, "url": ann.url})
    return response.output_text, links