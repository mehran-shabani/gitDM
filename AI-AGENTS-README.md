# AI Review Agents - CodeRabbit & Gemini

## 🎯 هدف کلی
این agents فقط برای **کامنت‌گذاری در Pull Request** طراحی شده‌اند. هیچ فایلی تغییر نمی‌دهند.

## 🤖 CodeRabbit Agent
**نقش**: Code-level review و compliance checking  
**تمرکز**: Technical details، کیفیت کد، تست coverage  
**کانفیگ**: `/.coderabbitai.yaml`  
**منابع**: فایل‌های `should-*` در هر فاز  

### نحوه عملکرد:
1. هر PR روی برنچ `feat/phase-*` را تشخیص می‌دهد
2. فایل‌های تغییر یافته را با `should-*.md` مقایسه می‌کند  
3. کامنت‌های مفصل inline و summary در PR می‌گذارد
4. جدول issues و checklist سازگاری Helssa ایجاد می‌کند

### قالب کامنت‌ها:
- **Summary Comment**: خلاصه کلی در بالای PR
- **Inline Comments**: روی خطوط مشکل‌دار کد
- **Issue Table**: جدول ساختاریافته مشکلات  
- **Helssa Compatibility**: چک‌لیست سازگاری

## 🧠 Gemini Agent  
**نقش**: High-level architecture review و strategic analysis  
**تمرکز**: معماری کلی، integration، cross-cutting concerns  
**کانفیگ**: `/gemini/gemini.md`  
**منابع**: همان فایل‌های `should-*` با دید strategic  

### نحوه عملکرد:
1. تحلیل معماری کلی فاز بر اساس `should-phase-architecture.md`
2. بررسی تاثیر بر فازهای آتی و گذشته
3. ارزیابی سازگاری عمیق با Helssa  
4. پیشنهادات strategic و بلندمدت

### قالب کامنت‌ها:
- **High-Level Summary**: ارزیابی کلی و امتیاز
- **Cross-Phase Analysis**: تاثیر بر سایر فازها
- **Strategic Recommendations**: پیشنهادات بلندمدت
- **Integration Deep-Dive**: تحلیل عمیق سازگاری

## 📋 منابع مجاز (هر دو agent)
```
/doc/phase1/should-*.md
/doc/phase2/should-*.md  
/doc/phase3/should-*.md
/doc/phase4/should-*.md
/doc/phase5/should-*.md
/doc/phase6/should-*.md
/doc/phase7/should-*.md
/doc/phase8/should-*.md
/cursoragent/AGENT.MD
/cursoragent/CODING_RULES.md
```

## 🚫 ممنوعیت‌های قطعی
- ❌ هیچ فایلی ایجاد نکن
- ❌ هیچ فایلی تغییر نده  
- ❌ فایل‌های خارج از `/doc/` نساز
- ❌ فقط کامنت در PR
- ❌ منابع خارجی استفاده نکن

## 🎛️ نحوه فعال‌سازی

### برای CodeRabbit:
```yaml
# در .coderabbitai.yaml
review:
  trigger: pull_request
  mode: comments_only
```

### برای Gemini:  
```markdown
# خواندن /gemini/gemini.md برای دستورالعمل‌ها
# منابع در /doc/phaseX/ قرار دارند
# فقط در PR comment کردن
```

## 📝 نمونه کامنت‌ها
- **CodeRabbit**: `/examples/coderabbit-comment-example.md`
- **Gemini**: `/examples/gemini-comment-example.md`

## 🔄 جریان کار
1. Developer PR می‌زند از `feat/phase-XX` به `develop`
2. CodeRabbit technical review می‌کند + جدول issues  
3. Gemini strategic analysis می‌کند + cross-phase impact
4. هر دو فقط کامنت می‌گذارند، هیچ فایلی تغییر نمی‌دهند
5. Developer بر اساس کامنت‌ها اصلاح می‌کند

## ⚠️ نکات مهم
- **پروژه ادامه Helssa است** - سازگاری اولویت اول
- **فقط should-* مرجع است** - suggestion-* صرفاً راهنما  
- **هر فاز مستقل** - cross-cutting concerns در Gemini
- **کامنت مفید** - با ارجاع مستقیم به منابع
- **بدون تغییر کد** - فقط review و پیشنهاد