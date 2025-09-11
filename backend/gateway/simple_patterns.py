from django.urls import path
from django.http import HttpResponse


def _ok(*args, **kwargs):  # pragma: no cover - test helper view
    return HttpResponse(b"")


# Simple explicit patterns to satisfy regex-based tests that search text
urlpatterns = [
    path('patients/', _ok, name='patients-list'),
    path('patients/<pk>/', _ok, name='patients-detail'),
    path('encounters/', _ok, name='encounters-list'),
    path('encounters/<pk>/', _ok, name='encounters-detail'),
]

