# Lightweight test stub for Celery to avoid external dependency in CI
# Provides shared_task decorator and minimal Celery class used by local code.
from types import SimpleNamespace
from typing import Any, Callable, Optional


def shared_task(_func: Optional[Callable] = None, **_kwargs: Any):
    def decorator(func: Callable) -> Callable:
        def delay(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
        setattr(func, "delay", delay)
        return func

    if _func is not None and callable(_func):
        return decorator(_func)
    return decorator


class Celery:
    def __init__(self, name: str) -> None:
        self.name = name

    def config_from_object(self, _obj: str, namespace: Optional[str] = None) -> None:  # noqa: ARG002
        return None

    def autodiscover_tasks(self) -> None:
        return None


# Submodule placeholder for "from celery.schedules import crontab"
schedules = SimpleNamespace()

def crontab(*_args: Any, **_kwargs: Any) -> str:  # minimal stub
    return "crontab-stub"

# Expose schedules.crontab
setattr(schedules, "crontab", crontab)
