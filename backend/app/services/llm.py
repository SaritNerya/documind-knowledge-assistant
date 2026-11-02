from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = (
    "אתה עוזר ארגוני שעונה על שאלות של עובדים. "
    "לא סופק לך כרגע שום מסמך או מידע על הארגון. "
    "לכן, אם השאלה נוגעת למדיניות, נהלים או מידע ספציפי של הארגון, "
    "ענה בדיוק: 'אין לי מידע על כך.' "
    "אל תנחש ואל תתאר מה בדרך כלל כתוב במסמכים כאלה."
)

def ask_llm(question: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content


RAG_SYSTEM_PROMPT = (
    "אתה עוזר ארגוני שעונה על שאלות של עובדים. "
    "תקבל קטעים מתוך מסמכי הארגון ושאלה. "
    "ענה אך ורק על סמך הקטעים שסופקו, בקצרה ובמדויק. "
    "אל תשתמש בידע כללי ואל תנחש. "
    "אם התשובה אינה מופיעה בקטעים, ענה בדיוק: 'לא מצאתי מידע על כך במסמכים.'"
)


def answer_from_context(question: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[מקור {i + 1}: {c['filename']}, עמוד {c['page']}]\n{c['content']}"
        for i, c in enumerate(chunks)
    )
    user_message = f"קטעים מהמסמכים:\n{context}\n\nשאלה: {question}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content