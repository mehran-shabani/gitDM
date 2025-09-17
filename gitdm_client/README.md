# GitDM Flutter Client

این پوشه یک اسکلت ساده برای کلاینت Flutter جهت ارتباط با بک‌اند Django/DRF پروژه‌ی GitDM است.

## اجرای اولیه
```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

> برای اندروید، اطمینان حاصل کنید که مجوز اینترنت در `android/app/src/main/AndroidManifest.xml` اضافه شده باشد:
> ```xml
> <uses-permission android:name="android.permission.INTERNET" />
> ```

## وابستگی‌ها
- `dio` برای درخواست‌های HTTP و اینترسپتور
- `provider` برای مدیریت ساده‌ی state
- `shared_preferences` برای ذخیره‌ی ساده‌ی توکن‌ها (برای محصول نهایی بهتر است از secure storage استفاده شود)
