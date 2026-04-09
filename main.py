"""OpenOMA Server — GraphQL server for the OpenOMA operational process framework."""

import uvicorn

from openoma_server.app import create_app
from openoma_server.settings import settings

app = create_app()


def main():
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()

