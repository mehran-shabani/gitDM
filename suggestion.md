## پیشنهادات برای تکمیل Review Server بر اساس نیازمندی‌های GitDM

| نقص شناسایی‌شده | پیشنهاد جبران/اقدام | توضیح اجرایی مختصر |
|-----------------|---------------------|---------------------|
| عدم وجود اسکن امنیتی استاتیک روی کد (OWASP/Bandit) | افزودن Rule `security_static_scan` در سطح global که Bandit (برای Python) و Trivy (برای Dockerfile) را اجرا کرده و گزارش را به‌صورت کامنت در PR درج می‌کند. | اجرای اسکریپت در GitHub Actions و پارس خروجی به فرمت MarkDown؛ شکست PR در سطح severity «high». |
| نبود معیار حداقل پوشش تست | تعریف Rule `test_coverage_threshold` در فاز `phase-08-testflow` با آستانه ≥ 80٪ و استفاده از Coverage.py؛ نتیجه در PR به‌عنوان کامنت. | استفاده از اکشن `pytest-coverage-comment`; در صورت نزول پوشش زیر 80٪، پرچم خطای بحرانی ثبت شود. |
| قانون کلی و مبهم برای Helssa Compatibility | گسترش Rule `helssa_compatibility` به «namespace و ورژن»؛ اعتبارسنجی import های `helssa.*` و بررسی `pyproject.toml` برای نسخه‌های پشتیبانی‌شده. | اسکریپت Python با ast parsing برای چک import؛ مقایسه نسخه با لیست مجاز. |
| فقدان Rule برای ایمنی Migration | ایجاد Rule `migration_safety` در فاز مدل‌ها؛ اسکریپت مقایسه مهاجرت‌ها جهت جلوگیری از عملیات خطرناک (حذف فیلد/جدول). | استفاده از `django-cautious-migrations`؛ در صورت شناسایی عملیات مخرب، اخطار «critical». |
| عدم آزمون RBAC و سطوح دسترسی | Rule `rbac_permission_tests` که اطمینان می‌دهد تمامی ViewSetها تست دسترسی حداقل دارند (استفاده از marker `rbac`). | Pytest plugin برای جستجوی تست‌هایی که از fixture `client_api` با کاربرهای متفاوت استفاده می‌کنند. |
| نبود تضمین پوشش تست End-to-End | Rule `e2e_flow_required` در فاز testflow برای الزام حداقل یک تست Cypress/Playwright که سناریوی کاربر اصلی را پوشش دهد. | اسکریپت بررسی وجود دایرکتوری `e2e/` و حداقل یک تست پاس شده. |
| عدم چک Consistency نام‌گذاری ماژول‌ها و مسیرها | Rule `naming_convention_linter` جهت اجرا شدن Flake8 + افزونه سفارشی برای enforcement نام‌گذاری Helssa و GitDM. | اضافه کردن pre-commit hook؛ خطا در صورت مغایرت. |
| فقدان مانع برای «print» یا logging ناایمن | Rule `no_plain_print` با ESLint/Flake8 plugin جهت منع `print()` و log سطح INFO داخل کد پروDUCTION. | خروجی در سطح error در PR. |
| عدم وارسی لایسنس وابستگی‌ها | Rule `dependency_license_check` که با `license-checker` لیست SPDX را بررسی می‌کند تا فقط لایسنس‌های مجاز (MIT, BSD, Apache-2.0) باقی بماند. | اجرا در GitHub Action و درج لیست پرخطر در کامنت. |

> اجرای این Ruleها خللی در «forbidden_actions» وارد نمی‌کند؛ همهٔ Ruleها فقط کامنت می‌گذارند و هیچ تغییری در سورس نمی‌دهند، مطابق محدودیت‌های GitDM.