# AGENT دستورالعمل فاز ۰۴ – API
- فقط فایل‌های این فاز را ایجاد/ویرایش کن.
- همه ViewSetها و Router طبق `should-coding-code.md` پیاده‌سازی شوند.
- احراز هویت JWT فعال باشد.
- **مهم**: هیچ endpoint عمومی برای ثبت‌نام کاربر ایجاد نکن. کاربران فقط از طریق Django Admin ساخته می‌شوند.
- تمام ForeignKey ها به User model باید از Django's ForeignKey استفاده کنند، نه UUID fields.
- پس از اتمام:
  - commit: "phase-04: api viewsets + jwt + timeline"
  - branch: `feat/phase-04-api`
  - PR به develop با لیبل‌های `phase-04`, `api`, `cursor-agent`