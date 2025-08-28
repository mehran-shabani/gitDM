# پیشنهاد کدنویسی – Versioning
- الگوی append-only برای همهٔ منابع بالینی
- ثبت snapshot کامل + diff خلاصه
- جلوگیری از لوپ با threadlocal guard
- امکان Revert با ساخت نسخهٔ جدید (بدون حذف تاریخچه)