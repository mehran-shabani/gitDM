from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        """
        بررسی می‌کند که کاربر درخواست‌دهنده نقش (role) برابر با 'admin' دارد یا خیر.
        
        این متد برای استفاده در کلاس‌های اجازه (DRF Permission) طراحی شده و مقدار True بازمی‌گرداند اگر:
        - شیء request دارای صفت `user` باشد و
        - آن `user` دارای صفت `role` باشد و
        - مقدار رشته‌ای `request.user.role.role` برابر `'admin'` باشد.
        
        در غیر این صورت False برمی‌گرداند.
        
        Parameters:
            request: شیء HTTP request (برای دسترسی به request.user).
            view: نمای (view) فعلی — در این متد استفاده‌ای از آن نمی‌شود اما توسط واسط DRF ارسال می‌شود.
        
        Returns:
            bool: True در صورت داشتن نقش ادمین، در غیر این صورت False.
        
        Notes:
            اگر `request.user.role` موجود باشد اما برابر None یا شی‌ای بدون صفت `role` باشد، دسترسی به `request.user.role.role` ممکن است AttributeError تولید کند.
        """
        return hasattr(request.user,'role') and request.user.role.role=='admin'

class IsDoctor(BasePermission):
    def has_permission(self, request, view):
        """
        بررسی می‌کند که کاربر درخواست‌دهنده نقش (role) برابر با 'doctor' دارد.
        
        تابع یک مقدار بولی بازمی‌گرداند: True اگر شیء request.user دارای صفت `role` بوده و مقدار `request.user.role.role` دقیقاً برابر رشته `'doctor'` باشد، در غیر این صورت False. این تابع برای استفاده در مجوزهای DRF طراحی شده تا دسترسی را فقط به کاربران با نقش دکتر اجازه دهد.
        """
        return hasattr(request.user,'role') and request.user.role.role=='doctor'