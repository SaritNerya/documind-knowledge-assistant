# Evaluation report: MIN_SCORE=0.3

- MIN_SCORE: 0.3
- Total questions: 57
- Answerable: 31
- Unanswerable: 26

## Retrieval
- Retrieval Hit Rate before threshold: 100.00%
- Retrieval Hit Rate after threshold: 100.00%
- Avg top score (answerable): 0.492
- Avg top score (unanswerable): 0.445
- Avg retrieval latency: 0.366s
- Duplicate chunks removed: 72

## Answer generation
- Answer Accuracy: 64.52%
- Refusal Rate: 92.31%
- Hallucination Rate: 7.69%
- Review-needed rate: 19.30%
- Avg answer latency: 1.113s

## Failed questions
- [answerable] כמה ימי חופשה לכל היותר אפשר לצבור לשנה הבאה?
  - failure_type: chunk_miss
  - retrieval_after_threshold: True
  - chunk_hit: False
  - answer_status: review_needed
- [answerable] באיזה מקרה צריך לצרף אישור רפואי למחלה?
  - failure_type: chunk_miss
  - retrieval_after_threshold: True
  - chunk_hit: False
  - answer_status: review_needed
- [answerable] מה מספר ימי העבודה מהבית המקסימלי בשבוע?
  - failure_type: review_needed
  - retrieval_after_threshold: True
  - chunk_hit: True
  - answer_status: review_needed
- [answerable] האם עובד חדש רשאי לעבוד מהבית בשבועיים הראשונים?
  - failure_type: chunk_miss
  - retrieval_after_threshold: True
  - chunk_hit: False
  - answer_status: review_needed
- [answerable] האם ישיבות צוות מתקיימות גם כאשר העובדים עובדים מהבית?
  - failure_type: chunk_miss
  - retrieval_after_threshold: True
  - chunk_hit: False
  - answer_status: review_needed
- [answerable] האם החברה משתתפת ברכישת שולחן או כיסא לעבודה מהבית?
  - failure_type: chunk_miss
  - retrieval_after_threshold: True
  - chunk_hit: False
  - answer_status: review_needed
- [answerable] תוך כמה זמן צריך להגיש בקשה להחזר הוצאות?
  - failure_type: chunk_miss
  - retrieval_after_threshold: True
  - chunk_hit: False
  - answer_status: review_needed
- [answerable] מי צריך לאשר מראש הוצאה עסקית בסכום של 650 ש"ח?
  - failure_type: chunk_miss
  - retrieval_after_threshold: True
  - chunk_hit: False
  - answer_status: review_needed
- [answerable] מה מתרחש ביום העבודה הראשון של עובד חדש?
  - failure_type: chunk_miss
  - retrieval_after_threshold: True
  - chunk_hit: False
  - answer_status: review_needed
- [answerable] באיזה שלב בתהליך הקליטה מתקיימת הדרכת מערכות ואבטחת מידע?
  - failure_type: chunk_miss
  - retrieval_after_threshold: True
  - chunk_hit: False
  - answer_status: review_needed
- [answerable] מתי מתקיימת שיחת המשוב הראשונה לעובד חדש?
  - failure_type: review_needed
  - retrieval_after_threshold: True
  - chunk_hit: True
  - answer_status: review_needed
- [unanswerable] האם העובדים מקבלים תקציב חודשי לרכישת ציוד משרדי לבית?
  - failure_type: hallucination
  - retrieval_after_threshold: False
  - chunk_hit: None
  - answer_status: incorrect_refusal
- [unanswerable] האם הוצאות על ארוחת צהריים במהלך יום עבודה מוכרות במקרה של שעות נוספות?
  - failure_type: hallucination
  - retrieval_after_threshold: False
  - chunk_hit: None
  - answer_status: incorrect_refusal

Keyword matching is a heuristic signal only; it is not a semantic equivalence check and should be treated as a review signal when uncertain.
