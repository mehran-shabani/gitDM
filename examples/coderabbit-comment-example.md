# نمونه کامنت CodeRabbit در PR

## 📋 CodeRabbit Review Summary

**Phase:** phase-02-models  
**Branch:** feat/phase-02-models  
**Files Changed:** 7 files  
**Architecture Compliance:** ✅  
**Test Coverage:** ❌  
**Helssa Compatibility:** ⚠️  

### Key Findings:
- ✅ مدل‌ها مطابق `/phases/phase-02-models/should-coding-code.md`
- ❌ تست‌های الزامی در `should-test-coding-code.md` ناقص
- ⚠️ فیلد `primary_doctor_id` نیازمند namespace سازگار با Helssa

### Issues Found:

| File | Line | Severity | Rule | Description |
|------|------|----------|------|-------------|
| patients_core/models.py | 8 | warning | helssa-compat | نام فیلد باید `helssa_doctor_id` باشد |
| diab_encounters/models.py | 15 | error | follow-should-files | فیلد `created_by` از should-* کپی نشده |
| tests/test_models.py | - | error | tests-required | تست relationship Patient→Encounter موجود نیست |

### Helssa Integration Check:
- ✅ UUID fields سازگار
- ❌ فیلد naming convention نیازمند تطبیق  
- ✅ JSONField usage مطابق Helssa standards
- ⚠️ Migration strategy نیازمند بررسی backward compatibility

### Recommendations:
1. **اولویت بالا**: اصلاح نام فیلدها برای سازگاری Helssa
2. **متوسط**: تکمیل تست‌های الزامی طبق should-test-coding-code.md  
3. **پایین**: افزودن docstring برای مدل‌ها

---

## Inline Comments:

### در فایل `patients_core/models.py`:
```python
primary_doctor_id = models.UUIDField()  # doctor مالک
```
**🤖 CodeRabbit:** این فیلد برای سازگاری با Helssa باید `helssa_doctor_id` نام‌گذاری شود  
**مرجع:** `/phases/phase-02-models/should-coding-code.md` + `/cursoragent/AGENT.MD` بخش سازگاری Helssa  
**پیشنهاد:** تغییر نام + migration برای rename field

### در فایل `diab_encounters/models.py`:
```python
created_by = models.UUIDField()
```
**🤖 CodeRabbit:** ✅ این فیلد دقیقاً مطابق should-coding-code.md پیاده‌سازی شده

### در فایل `tests/test_models.py`:
**🤖 CodeRabbit:** ❌ تست relationship بین Patient و Encounter موجود نیست  
**مرجع:** `/phases/phase-02-models/should-test-coding-code.md` خط 15-20  
**لازم:** افزودن `test_encounter_link` طبق نمونه should فایل