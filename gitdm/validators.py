from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
import re


def validate_national_id(value):
    """
    اعتبارسنجی کد ملی ایرانی
    """
    if not value:
        return
    
    # حذف کاراکترهای غیرعددی
    value = re.sub(r'\D', '', str(value))
    
    # بررسی طول
    if len(value) != 10:
        raise ValidationError('کد ملی باید 10 رقم باشد')
    
    # بررسی عدم تکرار ارقام
    if len(set(value)) == 1:
        raise ValidationError('کد ملی نمی‌تواند همه ارقام یکسان باشد')
    
    # محاسبه رقم کنترل
    check_sum = sum(int(value[i]) * (10 - i) for i in range(9)) % 11
    check_digit = int(value[9])
    
    if check_sum < 2:
        if check_digit != check_sum:
            raise ValidationError('کد ملی نامعتبر است')
    else:
        if check_digit != 11 - check_sum:
            raise ValidationError('کد ملی نامعتبر است')


def validate_medical_code(value):
    """
    اعتبارسنجی کد نظام پزشکی
    """
    if not value:
        return
    
    # فرمت کلی: حروف و اعداد، حداقل 5 کاراکتر
    if not re.match(r'^[A-Za-z0-9]{5,}$', value):
        raise ValidationError('کد نظام پزشکی باید حداقل 5 کاراکتر شامل حروف و اعداد باشد')


def validate_age_range(birth_date):
    """
    اعتبارسنجی محدوده سنی منطقی
    """
    if not birth_date:
        return
    
    today = timezone.now().date()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    if age < 0:
        raise ValidationError('تاریخ تولد نمی‌تواند در آینده باشد')
    
    if age > 150:
        raise ValidationError('سن نمی‌تواند بیشتر از 150 سال باشد')


def validate_hba1c_value(value):
    """
    اعتبارسنجی مقدار HbA1c
    """
    if value is None:
        return
    
    # محدوده طبیعی HbA1c: 4-18%
    if not (4.0 <= float(value) <= 18.0):
        raise ValidationError('مقدار HbA1c باید بین 4 تا 18 درصد باشد')


def validate_blood_glucose(value):
    """
    اعتبارسنجی مقدار قند خون
    """
    if value is None:
        return
    
    # محدوده منطقی: 20-800 mg/dL
    if not (20 <= float(value) <= 800):
        raise ValidationError('مقدار قند خون باید بین 20 تا 800 mg/dL باشد')


def validate_blood_pressure(systolic, diastolic):
    """
    اعتبارسنجی فشار خون
    """
    if systolic is None or diastolic is None:
        return
    
    systolic = float(systolic)
    diastolic = float(diastolic)
    
    # محدوده منطقی
    if not (60 <= systolic <= 250):
        raise ValidationError('فشار سیستولیک باید بین 60 تا 250 باشد')
    
    if not (40 <= diastolic <= 150):
        raise ValidationError('فشار دیاستولیک باید بین 40 تا 150 باشد')
    
    # سیستولیک باید بیشتر از دیاستولیک باشد
    if systolic <= diastolic:
        raise ValidationError('فشار سیستولیک باید بیشتر از دیاستولیک باشد')


def validate_medication_dose(dose_str):
    """
    اعتبارسنجی فرمت دوز دارو
    """
    if not dose_str:
        return
    
    # فرمت‌های معتبر: "500mg", "1.5g", "10units", "2ml"
    pattern = r'^\d+(\.\d+)?\s*(mg|g|ml|units?|mcg|iu|cc)$'
    if not re.match(pattern, dose_str.lower().strip()):
        raise ValidationError('فرمت دوز نامعتبر است. مثال معتبر: 500mg, 1.5g, 10units')


def validate_encounter_date(occurred_at):
    """
    اعتبارسنجی تاریخ مواجهه
    """
    if not occurred_at:
        return
    
    encounter_date = occurred_at.date() if hasattr(occurred_at, 'date') else occurred_at
    today = timezone.now().date()
    
    # نمی‌تواند بیشتر از 1 سال آینده باشد
    if encounter_date > today + timedelta(days=365):
        raise ValidationError('تاریخ مواجهه نمی‌تواند بیشتر از یک سال آینده باشد')
    
    # نمی‌تواند بیشتر از 10 سال گذشته باشد (برای محدود کردن داده‌های قدیمی)
    if encounter_date < today - timedelta(days=3650):
        raise ValidationError('تاریخ مواجهه نمی‌تواند بیشتر از 10 سال گذشته باشد')