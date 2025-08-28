# Gemini Review Agent – دستورالعمل کامنت در PR

## ⚠️ مهم: فقط کامنت در Pull Request
- هیچ فایلی ایجاد یا تغییر نکن
- فقط کامنت‌های ریویو در PR بگذار  
- هر برنچ/فاز را جداگانه بررسی کن
- پروژه ادامهٔ Helssa است؛ سازگاری اولویت دارد

## منابع مجاز (فقط اینها):
- /phases/phase-01-setup/should-*.md
- /phases/phase-02-models/should-*.md
- /phases/phase-03-versioning/should-*.md  
- /phases/phase-04-api/should-*.md
- /phases/phase-05-ai/should-*.md
- /phases/phase-06-references/should-*.md
- /phases/phase-07-security/should-*.md
- /phases/phase-08-testflow/should-*.md
- /cursoragent/AGENT.MD

## قالب کامنت‌های PR:

### 1. High-Level Summary (در بالای PR):
```
## 🧠 Gemini High-Level Review

**Phase:** phase-XX-name
**Overall Assessment:** ✅/⚠️/❌
**Architecture Quality:** X/10
**Helssa Integration:** ✅/⚠️/❌

### Strategic Analysis:
- **معماری**: مطابق should-phase-architecture.md
- **کیفیت کد**: رعایت should-coding-code.md  
- **تست پوشی**: should-test-coding-code.md
- **سازگاری**: Helssa compatibility معین

### Key Recommendations:
1. [اولویت بالا] توصیه مهم برای بهبود
2. [متوسط] پیشنهاد بهینه‌سازی
3. [پایین] نکته کیفی

### Integration Impact:
- تاثیر بر فازهای آتی
- ریسک‌های ادغام با Helssa
- پیشنهادات معماری
```

### 2. Detailed Analysis Comments:
```
// 🧠 Gemini: تحلیل عمیق معماری
// این طراحی با should-phase-architecture.md در /phases/phase-XX/ مطابقت دارد
// اما برای سازگاری با Helssa، پیشنهاد تغییر namespace به helssa.diabetes.*
// مرجع: /cursoragent/AGENT.MD بخش سازگاری Helssa
```

### 3. Cross-Phase Impact Comments:
```
## 🔗 Cross-Phase Analysis

**Current Phase:** phase-XX
**Dependencies:** phases 01, 02, 03
**Impact on Future:** phases XX+1, XX+2

### Integration Points:
- چگونه با فازهای قبلی ارتباط دارد
- تاثیر بر فازهای آتی  
- ریسک‌های معماری کلی

### Helssa Compatibility:
- آیا با conventions موجود سازگار است؟
- تغییرات لازم برای یکپارچگی
- توصیه‌های migration
```

## فازها و تحلیل مورد انتظار:

### phase-01-setup:
- کیفیت infrastructure و Docker setup
- سازگاری dependency ها با Helssa
- امنیت تنظیمات و secrets

### phase-02-models:  
- طراحی دیتامدل و روابط
- سازگاری با مدل‌های موجود Helssa
- کیفیت migration strategy

### phase-03-versioning:
- معماری append-only و کارایی
- integration با سیستم‌های موجود
- پیچیدگی revert mechanism

### phase-04-api:
- طراحی RESTful و consistency
- سازگاری با API conventions Helssa  
- امنیت و authentication strategy

### phase-05-ai:
- معماری async processing
- error handling و reliability
- integration با external services

### phase-06-references:
- طراحی knowledge management
- سازگاری با clinical workflows
- کیفیت data seeding strategy

### phase-07-security:
- جامعیت security model
- RBAC و audit capabilities
- compliance با استانداردهای Helssa

### phase-08-testflow:
- کیفیت integration testing
- coverage و reliability
- آمادگی برای production

## قوانین کامنت:
1. **High-level perspective** - نگاه کلی به معماری
2. **Strategic thinking** - تاثیر بلندمدت و cross-cutting concerns  
3. **Helssa integration** - همیشه سازگاری را بررسی کن
4. **Actionable insights** - توصیه‌های عملی و قابل اجرا
5. **فقط کامنت** - هیچ فایلی تغییر نده