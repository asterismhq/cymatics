"""Application-level settings for the FastAPI template."""

from pydantic import Field
from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    """Minimal settings exposed to the dependency container."""

    app_name: str = Field(
        default="fapi-tmpl",
        alias="FAPI_TMPL_APP_NAME",
        description="Public-facing service name reported in responses and logs.",
    )
    use_mock_greeting: bool = Field(
        default=False,
        alias="FAPI_TMPL_USE_MOCK_GREETING",
        description="Toggle to inject the mock greeting service for local dev and tests.",
    )


settings = AppSettings()
