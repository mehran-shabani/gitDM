/// مدل مینیمال بیمار.
/// فیلدها ممکن است در بک‌اند شما مختلف باشند.
/// اینجا چند فیلد رایج را در نظر می‌گیریم؛ در صورت نیاز با API واقعی هماهنگ کنید.
class Patient {
  final int id;
  final String fullName;

  Patient({required this.id, required this.fullName});

  factory Patient.fromJson(Map<String, dynamic> json) {
    // ابتدا full_name یا fullName را بررسی می‌کنیم
    final full = (json['full_name'] ?? json['fullName'])?.toString() ?? '';
    final first = (json['first_name'] ?? json['firstName'] ?? '').toString();
    final last = (json['last_name'] ?? json['lastName'] ?? '').toString();
    
    // اگر full_name موجود بود، از آن استفاده می‌کنیم
    final combined = full.isNotEmpty
        ? full
        : (first.isNotEmpty && last.isNotEmpty)
            ? '$first $last'
            : (first.isNotEmpty ? first : (last.isNotEmpty ? last : ''));

    // در صورت عدم وجود نام ترکیبی، json['name'] را به عنوان نام کامل در نظر می‌گیریم
    final finalName = combined.isNotEmpty 
        ? combined 
        : (json['name']?.toString() ?? '');

    // پارس ایمن ID - پشتیبانی از int، string، و double
    int parsedId = 0;
    final rawId = json['id'];
    if (rawId is int) {
      parsedId = rawId;
    } else if (rawId is String) {
      parsedId = int.tryParse(rawId) ?? 0;
    } else if (rawId is double) {
      parsedId = rawId.toInt();
    }

    return Patient(
      id: parsedId,
      fullName: finalName.isNotEmpty ? finalName : 'نام‌نامشخص',
    );
  }
}