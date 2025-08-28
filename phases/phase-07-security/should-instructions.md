# دستورالعمل اجرای فاز ۰۷
1) افزودن اپ security به INSTALLED_APPS
2) اجرای migrate برای AuditLog و Role
3) افزودن AuditMiddleware به settings
4) ایجاد کاربران و Role در ادمین
5) تست export: GET /api/export/patient/{uuid}