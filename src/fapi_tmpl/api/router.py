"""HTTP routes exposed by the FastAPI template."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..protocols.greeting_service_protocol import GreetingServiceProtocol
from .dependencies import get_greeting_service

router = APIRouter()


class GreetingResponse(BaseModel):
    message: str


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return a simple health status payload."""
    return {"status": "ok"}


@router.get("/hello/{name}", response_model=GreetingResponse)
async def say_hello(
    name: str,
    greeter: GreetingServiceProtocol = Depends(get_greeting_service),
) -> GreetingResponse:
    greeting = greeter.generate_greeting(name)
    return GreetingResponse(message=greeting)
