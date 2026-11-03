import json
import sys
import time
from pathlib import Path

# מאפשר לייבא את קוד ה-Backend
BACKEND = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.api.chat import MIN_SCORE, NOT_FOUND_ANSWER
from app.core.database import SessionLocal
from app.services.llm import answer_from_context
from app.services.retrieval import search_chunks

USER_ID = 1  # ← המשתמש שהעלה את מסמכי הדוגמה
HERE = Path(__file__).parent


def average(values):
    return sum(values) / len(values) if values else 0.0

def keyword_groups(q):
    """כל קבוצה = חלופות. תשובה נכונה אם מכל קבוצה מופיעה לפחות מילה אחת."""
    return [[k] if isinstance(k, str) else k for k in q["keywords"]]


def matches(text, groups):
    return all(any(alt in text for alt in group) for group in groups)

def main():
    questions = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    db = SessionLocal()
    results = []

    for q in questions:
        start = time.perf_counter()
        chunks = search_chunks(db, USER_ID, q["question"])
        relevant = [c for c in chunks if c["score"] >= MIN_SCORE]
        if relevant:
            answer = answer_from_context(q["question"], relevant)
        else:
            answer = NOT_FOUND_ANSWER
        elapsed = time.perf_counter() - start

        refused = "לא מצאתי" in answer
        top_score = chunks[0]["score"] if chunks else 0.0

        if q["type"] == "answerable":
            groups = keyword_groups(q)
            retrieved_text = " ".join(c["content"] for c in chunks)
            retrieval_hit = any(c["filename"] == q["source"] for c in chunks)
            chunk_hit = matches(retrieved_text, groups)
            correct = (not refused) and matches(answer, groups)
        else:
            retrieval_hit = None
            chunk_hit = None
            correct = refused
        
        results.append({
            "question": q["question"],
            "type": q["type"],
            "retrieval_hit": retrieval_hit,
            "correct": correct,
            "top_score": round(top_score, 3),
            "latency": round(elapsed, 2),
            "answer": answer,
            "chunk_hit": chunk_hit,
            "retrieved": [
                {"file": c["filename"], "score": round(c["score"], 3), "text": c["content"]}
                for c in chunks
            ],
        })

    (HERE / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    answerable = [r for r in results if r["type"] == "answerable"]
    unanswerable = [r for r in results if r["type"] == "unanswerable"]

    print("\n===== סיכום =====")
    print(f"MIN_SCORE: {MIN_SCORE}")
    print(f"שאלות עם תשובה: {len(answerable)} | בלי תשובה: {len(unanswerable)}")
    print(f"דיוק שליפה (המסמך הנכון בין התוצאות): "
          f"{average([r['retrieval_hit'] for r in answerable]):.0%}")
    print(f"דיוק שליפה ברמת הקטע (העובדה בתוך הקטעים שנשלפו): "
          f"{average([r['chunk_hit'] for r in answerable]):.0%}")
    print(f"דיוק תשובות: {average([r['correct'] for r in answerable]):.0%}")
    refusal = average([r["correct"] for r in unanswerable])
    print(f"סירוב נכון בשאלות בלי תשובה: {refusal:.0%} (שיעור המצאות: {1 - refusal:.0%})")
    print(f"זמן תגובה ממוצע: {average([r['latency'] for r in results]):.2f} שניות")
    print(f"ציון שליפה ממוצע, שאלות עם תשובה: "
          f"{average([r['top_score'] for r in answerable]):.3f}")
    print(f"ציון שליפה ממוצע, שאלות בלי תשובה: "
          f"{average([r['top_score'] for r in unanswerable]):.3f}")

    print("\n===== שאלות שנכשלו =====")
    for r in results:
        if not r["correct"] or r["retrieval_hit"] or r["chunk_hit"] is False:
            print(f"- [{r['type']}] {r['question']}")
            print(f"  ציון: {r['top_score']} | שליפה: {r['retrieval_hit']}")
            print(f"  chunk_hit: {r['chunk_hit']}")
            print(f"  תשובה: {r['answer'][:120]}")


if __name__ == "__main__":
    main()