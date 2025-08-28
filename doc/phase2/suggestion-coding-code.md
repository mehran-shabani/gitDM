# پیشنهاد کدنویسی – مدل‌ها
- Patient: اطلاعات پایه بیمار + مالک پزشک
- Encounter: ثبت ویزیت دیابت (SOAP, vitals, assessment, plan)
- LabResult: نتایج آزمایش (HbA1c, FBS, …)
- MedicationOrder: نسخه دارویی
- ClinicalReference: رفرنس‌های بالینی (ADA, WHO)
- AISummary: خلاصه‌سازی هوش برای هر Encounter/Lab/Medication
- RecordVersion: نسخه‌گذاری append-only