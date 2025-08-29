from .models import AuditLog
import logging

logger = logging.getLogger(__name__)

class AuditMiddleware:
    def __init__(self, get_response):
        """
        یک خطی: سازنده‌ی میدل‌ور که Callable بعدی (لایه‌ی بعدی درخواست) را نگهداری می‌کند.
        
        توضیح: نمونه‌ی میدل‌ور را مقداردهی اولیه می‌کند و ارجاع به تابع یا callable لایه‌ی بعدی در زنجیره‌ی پردازش درخواست را در self.get_response ذخیره می‌نماید تا هنگام فراخوانی میدل‌ور بتواند درخواست را به لایه‌ی بعدی پاس دهد.
        
        Parameters:
            get_response (callable): تابع یا callable مورد انتظار از چارچوب وب که یک شیء Request را گرفته و یک شیء Response بازمی‌گرداند؛ این مقدار در self.get_response نگهداری می‌شود.
        """
        self.get_response = get_response

    def __call__(self, request):
        """
        پردازش یک درخواست WSGI/Django: فراخوانی لایه بعدی، ثبت غیرتهاجمی رکورد AuditLog و بازگرداندن پاسخ.
        
        این متد ابتدا درخواست را به لایه بعدی می‌فرستد و پاسخ دریافتی را بازمی‌گرداند. پس از دریافت پاسخ، تلاش می‌کند یک رکورد AuditLog ایجاد کند که شامل شناسه کاربر (در صورت احراز هویت)، مسیر، متد HTTP، کد وضعیت پاسخ و آدرس کلاینت است. شناسه کاربر به‌صورت UUID تعیین‌پذیر از مقدار عددی id کاربر ساخته می‌شود (uuid5 با namespace NAMESPACE_DNS و رشته‌ی 'user-{id}') تا از افشای شناسه‌های خام جلوگیری شود. هر گونه خطا در فرایند ثبت لاگ نادیده گرفته می‌شود تا عملکرد میدلور روی جریان پاسخ‌دهی تاثیری نداشته باشد.
        
        Parameters:
            request: شیء درخواست Django که حداقل صفات موردنیاز (`path`, `method`, `META`, و در صورت وجود `user`) را دارد.
        
        Returns:
            response: شیء پاسخ بازگشتی از لایه بعدی (همان شیء‌ای که از `self.get_response(request)` دریافت شده).
        """
        response = self.get_response(request)
        try:
            user_id = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_id = request.user.id
            
            AuditLog.objects.create(
                user_id=user_id,
                path=request.path,
                method=request.method,
                status_code=response.status_code,
                meta={"remote_addr": request.META.get('REMOTE_ADDR')}
            )
        except Exception as e:
            logger.error("Failed to create audit log: %s", e)
        return response