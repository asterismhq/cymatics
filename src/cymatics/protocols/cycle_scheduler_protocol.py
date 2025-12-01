"""Protocol for the cycle scheduler service."""

from typing import Protocol

from cymatics.models import QueueStatus


class CycleSchedulerProtocol(Protocol):
    """Interface for the directory watching and task scheduling service."""

    async def start(self) -> None:
        """Start the scheduler and begin monitoring directories."""
        ...

    async def stop(self) -> None:
        """Stop the scheduler and cleanup."""
        ...

    def get_queue_status(self) -> QueueStatus:
        """Get the current status of the processing queue."""
        ...
