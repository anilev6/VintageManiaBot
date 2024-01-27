import logging
from logging import handlers

import asyncio
import sys
import time

import re
import functools

NAME = "logs/VintageMania.log"


# --------------------------------------UTILS-----------------------------------------------
def redacted(error_msg: str) -> str:
    """this is a filter function for errors to cover unnecessary info"""
    error_msg = re.sub(r"api-\w{4}-\w{4}-\w{4}", "[REDACTED-API-KEY]", error_msg)
    error_msg = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
        "[REDACTED-EMAIL]",
        error_msg,
    )
    error_msg = re.sub(r"(https://api.telegram.org/).*", r"\1 [REDACTED]", error_msg)
    error_msg = re.sub(r"(https://api.ebay.com/).*", r"\1 [REDACTED]", error_msg)
    error_msg = re.sub(r"(https://api.openai.com/v1/).*", r"\1 [REDACTED]", error_msg)
    return error_msg


# -------------------------------------SET UP-----------------------------------------------
class CustomStreamHandler(logging.StreamHandler):
    def __init__(self, stream=sys.stdout):
        super().__init__(stream=stream)

    def emit(self, record):
        # replace emoji etc
        try:
            msg = self.format(record)
            stream = self.stream
            # Encoding with 'backslashreplace' to avoid UnicodeEncodeError
            stream.write(
                msg.encode("utf-8", errors="backslashreplace").decode("utf-8")
                + self.terminator
            )
            self.flush()
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        CustomStreamHandler(),
        # automatic log rotation
        handlers.RotatingFileHandler(NAME, maxBytes=2 * 1024 * 1024, backupCount=5),
    ],
)

# get rid of the annoying logs
logging.getLogger("http").propagate = False
logging.getLogger("httpx").propagate = False
logging.getLogger("aiohttp").propagate = False

logger = logging.getLogger(__name__)


# exclude the annoying openai log / does not work

# class ExcludeOpenAILogFilter(logging.Filter):
#     def filter(self, record):
#         return not (
#             "message='OpenAI API response' path=https://api.openai.com/v1/"
#             in record.getMessage()
#         )

# logger.addFilter(ExcludeOpenAILogFilter())

# -------------------------------------------------------------------------------------------
# log rotation / does not work

# this package wouldn't install if you don't use python2
# from concurrent_log_handler import ConcurrentRotatingFileHandler

# rotation_handler = ConcurrentRotatingFileHandler(NAME, maxBytes=10000, backupCount=5)
# logger.addHandler(rotation_handler)


# -----------------------------------UNIVERSAL DEBUG DECORATOR--------------------------------
def time_log_decorator(func):
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()

            logger.info(f"Entering {func.__name__}")

            try:
                result = await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {redacted(str(e))}")
                raise e

            else:
                elapsed_time = time.time() - start_time
                logger.info(
                    f"Exiting {func.__name__}. Execution time: {elapsed_time:.4f} seconds"
                )
                return result

        return async_wrapper
    else:

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            logger.info(f"Entering {func.__name__}")

            try:
                result = func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {redacted(str(e))}")
                raise e
            else:
                elapsed_time = time.time() - start_time
                logger.info(
                    f"Exiting {func.__name__}. Execution time: {elapsed_time:.4f} seconds"
                )
                return result

        return wrapper


# -----------------------------------------TEST DECORATOR-----------------------------------
@time_log_decorator
def test_function():
    print("Inside a synchronous function")


@time_log_decorator
async def async_test_function():
    print("Entering an asynchronous function")
    await asyncio.sleep(1)
    print("Exiting an asynchronous function")


# Test the decorator
if __name__ == "__main__":
    test_function()
    asyncio.run(async_test_function())
