"""FastAPI application entry point for the template."""

from importlib import metadata

from fastapi import FastAPI

from .router import router


def get_safe_version(package_name: str, fallback: str = "0.1.0") -> str:
    """
    Safely get the version of a package.
    Args:
            package_name: Name of the package
            fallback: Default version if retrieval fails
    Returns:
            Version string
    """
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        # Optionally log when fallback is used
        return fallback


app = FastAPI(title="fapi-tmpl", version=get_safe_version("fapi-tmpl"))
app.include_router(router)
