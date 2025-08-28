# معماری فاز ۰۲ – مدل‌ها

- Node اصلی: Patient, Encounter, LabResult, MedicationOrder
- Support Node: ClinicalReference, AISummary, RecordVersion
- ارتباطات:
  Patient 1..* Encounter
  Encounter 0..* LabResult
  Encounter 0..* MedicationOrder
  Encounter 0..* AISummary
  Resource → RecordVersion (append-only)
- پایگاه‌داده: Postgres 16 با JSONField برای محتوای ساختاریافته