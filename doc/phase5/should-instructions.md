# دستورالعمل اجرای فاز ۰۵
1) تنظیم OPENAI_API_KEY در .env
2) راه‌اندازی worker: docker compose up -d worker beat
3) ثبت Encounter/Lab/Medication جدید
4) مشاهده ایجاد خودکار AISummary در DB