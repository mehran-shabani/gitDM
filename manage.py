#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main() -> None:
    """اجرای ابزار خط‌دستور مدیریتی جنگو (پیام خطا کوتاه، بدون traceback)."""
    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    # Determine settings module based on environment
    settings_mode = os.getenv('SETTINGS_MODE', 'full')
    if settings_mode == 'simple':
        settings_module = 'config.simple_settings'
    else:
        settings_module = 'config.settings'
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)
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
