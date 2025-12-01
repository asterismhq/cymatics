from functools import lru_cache
from typing import TYPE_CHECKING

from ..config import AppSettings
from ..protocols.greeting_service_protocol import GreetingServiceProtocol
from ..services.greeting_service import GreetingService

if TYPE_CHECKING:  # pragma: no cover - import only for type checking
    pass


@lru_cache()
def get_app_settings() -> AppSettings:
    return AppSettings()


def get_greeting_service() -> GreetingServiceProtocol:
    settings = get_app_settings()

    if settings.use_mock_greeting:
        from dev.mocks.services.mock_greeting_service import MockGreetingService

        return MockGreetingService()

    return GreetingService()
