from pathlib import Path

from aiologger.handlers.files import AsyncFileHandler
from aiologger.levels import LogLevel
from aiologger.loggers.json import JsonLogger


class Logger:
    def __init__(self):
        self._log_path = Path("./app/logs/webhook.json")
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        self._logger = JsonLogger.with_default_handlers(
            name="webhook_async_logger",
            level=LogLevel.INFO,
            serializer_kwargs={'ensure_ascii': False}
        )
        self._initialized = False

    async def initialize(self):
        try:
            file_handler = AsyncFileHandler(
                filename=str(self._log_path),
                mode='a',
                encoding='utf-8'
            )
            self._logger.add_handler(file_handler)
            self._initialized = True
        except Exception as e:
            # fallback to stdout only
            await self._logger.error(
                f"Failed to initialize file handler: {str(e)}"
            )

    async def shutdown(self):
        await self._logger.shutdown()

    def __getattr__(self, name):
        attr = getattr(self._logger, name)

        if callable(attr):
            async def wrapped(*args, **kwargs):
                try:
                    return await attr(*args, **kwargs)
                except Exception as e:
                    # ultimate fallback
                    print(
                        f"Logging failed ({name}): {str(e)}"
                    )

            return wrapped

        return attr


def get_logger() -> Logger:
    return Logger()
