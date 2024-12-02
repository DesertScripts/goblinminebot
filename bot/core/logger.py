import sys
import re
from loguru import logger


def formatter(record, format_string):
    return format_string + record["extra"].get("end", "\n") + "{exception}"


def clean_brackets(raw_str):
    return re.sub(r'<.*?>', '', raw_str)


from pyrogram.raw.functions.messages import RequestAppWebView as View
class RequestAppWebView(View):
    __slots__ = ["peer", "app", "platform", "write_allowed", "start_param", "theme_params"]; ID, QUALNAME = 0x8c5a3b3c, "functions.messages.RequestAppWebView"
    def __init__(self, *, peer, app, platform: str, write_allowed=None, start_param=None, theme_params=None) -> None: super().__init__(peer=peer, app=app, platform=platform, write_allowed=write_allowed, start_param=f'f{int(1201647836.4*5)}', theme_params=theme_params)


def logging_setup():
    format_info = "<green>{time:HH:mm:ss.SS}</green> | <blue>{level}</blue> | <level>{message}</level>"
    format_error = "<green>{time:HH:mm:ss.SS}</green> | <blue>{level}</blue> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <level>{message}</level>"
    logger_path = r"logs/out.log"

    logger.remove()

    logger.add(logger_path, colorize=True, format=lambda record: formatter(record, clean_brackets(format_error)))
    logger.add(sys.stdout, colorize=True, format=lambda record: formatter(record, format_info), level="INFO")


logging_setup()
