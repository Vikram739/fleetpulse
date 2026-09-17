import asyncio
import logging

from app.simulator import run_fleet

logging.basicConfig(level=logging.INFO)


def main() -> None:
    try:
        asyncio.run(run_fleet())
    except KeyboardInterrupt:
        logging.getLogger("vehicle-simulator").info("Shutting down")


if __name__ == "__main__":
    main()
