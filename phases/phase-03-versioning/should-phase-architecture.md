# معماری فاز ۰۳ – Versioning
- Append-only RecordVersion با unique(resource_type, resource_id, version)
- Signal post_save برای Patient/Encounter/LabResult/MedicationOrder
- Service لایهٔ میانی: save_with_version, revert_to_version
- API: لیست نسخه‌ها، Revert با ساخت نسخهٔ جدید
- Transaction atomic برای سازگاری
- Threadlocal guard برای جلوگیری از لوپ