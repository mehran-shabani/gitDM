#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main() -> None:
    """
    اجرای ابزار خط‌دستور مدیریتی جنگو.
    
    این تابع:
    - در صورت نبود متغیر محیطی، DJANGO_SETTINGS_MODULE را به 'config.settings' مقداردهی پیش‌فرض می‌کند.
    - تلاش می‌کند تا تابع `execute_from_command_line` از بسته `django.core.management` را وارد کند؛ در صورت عدم موفقیت پیام خطا روی stderr چاپ شده و فرآیند با وضعیت خروج 1 خاتمه می‌یابد.
    - `execute_from_command_line(sys.argv)` را اجرا می‌کند تا فرمان‌های مدیریت پروژه را پردازش کند.
    - در صورت اجرای موفق، فرآیند با وضعیت خروج 0 خاتمه می‌یابد؛ در صورت بروز هر استثنایی، پیام خطا روی stderr چاپ شده و با وضعیت خروج 1 خاتمه می‌یابد.
    
    توجه: تابع مقدار بازگشتی ندارد و رفتار اصلی آن آغاز و مدیریت چرخه‌زندگی ابزار خط‌دستور جنگو با استفاده از متغیرهای محیطی و آرگومان‌های خط‌دستور است.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        print("Error: Couldn't import Django. Check installation and PYTHONPATH.", file=sys.stderr)
        sys.exit(1)
    
    try:
        execute_from_command_line(sys.argv)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
