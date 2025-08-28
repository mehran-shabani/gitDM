# دستورالعمل اجرای فاز ۰۶
1) makemigrations/migrate برای تغییرات مدل‌ها
2) اجرای Seeding: `python manage.py seed_refs_diabetes`
3) ثبت Encounter/Lab/Medication آزمایشی → اجرای task خلاصه‌سازی → بررسی اضافه‌شدن refs
4) فیلتر API: `/api/refs/?topic=diabetes&year=2025`