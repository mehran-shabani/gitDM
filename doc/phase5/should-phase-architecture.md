# معماری فاز ۰۵ – AI Integration
- Event: post_save روی Encounter/Lab/Medication
- Queue: Celery task summarize_record
- External: OpenAI ChatCompletion (gpt-4o-mini)
- Storage: AISummary در DB + ارتباط با ClinicalReference
- Error handling: retry + backoff