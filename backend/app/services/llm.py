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