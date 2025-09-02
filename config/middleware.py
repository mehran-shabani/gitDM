from django.http import JsonResponse
from django_ratelimit.exceptions import Ratelimited


class RateLimitMiddleware:
    """
    Middleware to handle rate limit exceptions and return proper API responses.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Ratelimited:
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'detail': 'You have exceeded the rate limit for this endpoint. Please try again later.'
            }, status=429)
        return response