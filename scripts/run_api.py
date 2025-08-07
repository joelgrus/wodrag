#!/usr/bin/env python3
"""Script to run the wodrag API server."""

import uvicorn
from wodrag.api.config import get_settings


def main() -> None:
    """Run the API server."""
    settings = get_settings()
    
    uvicorn.run(
        "wodrag.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()