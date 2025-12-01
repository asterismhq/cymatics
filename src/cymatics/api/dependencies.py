"""Dependency injection for cymatics API."""

from functools import lru_cache
from typing import Optional

from cymatics.config import AppSettings
from cymatics.protocols import CycleSchedulerProtocol, TransmutationServiceProtocol
from cymatics.services import CycleSchedulerService, TransmutationService

# Global service instances (lazily initialized)
_transmutation_service: Optional[TransmutationServiceProtocol] = None
_cycle_scheduler: Optional[CycleSchedulerProtocol] = None


@lru_cache()
def get_app_settings() -> AppSettings:
    """Get application settings (cached)."""
    return AppSettings()


def get_transmutation_service() -> TransmutationServiceProtocol:
    """Get the transmutation service instance."""
    global _transmutation_service

    settings = get_app_settings()

    if settings.use_mock_transmutation:
        from dev.mocks.services.mock_transmutation_service import (
            MockTransmutationService,
        )

        return MockTransmutationService()

    if _transmutation_service is None:
        _transmutation_service = TransmutationService(
            model_name=settings.whisper_model,
            unload_timeout=settings.model_unload_timeout,
        )

    return _transmutation_service


def get_cycle_scheduler() -> CycleSchedulerProtocol:
    """Get the cycle scheduler instance."""
    global _cycle_scheduler

    if _cycle_scheduler is None:
        settings = get_app_settings()
        _cycle_scheduler = CycleSchedulerService(
            data_dir=settings.data_dir,
            transmutation_service=get_transmutation_service(),
            poll_interval=settings.cycle_poll_interval,
            debounce_seconds=settings.debounce_seconds,
        )

    return _cycle_scheduler


def reset_services() -> None:
    """Reset service instances (for testing)."""
    global _transmutation_service, _cycle_scheduler
    _transmutation_service = None
    _cycle_scheduler = None
    get_app_settings.cache_clear()
