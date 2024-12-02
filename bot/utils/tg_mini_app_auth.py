import asyncio
import json
from typing import Dict
from urllib.parse import (
    parse_qs,
    unquote,
)

import pyrogram
from better_proxy import Proxy
from pyrogram.errors import (
    AuthKeyUnregistered,
    FloodWait,
    Unauthorized,
    UserDeactivated,
)
from pyrogram.raw.functions.messages.request_app_web_view import RequestAppWebView
from pyrogram.raw.types.input_bot_app_short_name import InputBotAppShortName

from bot.utils.logger import logger


class TelegramMiniAppAuth:
    def __init__(
        self, telegram_client: pyrogram.client.Client, proxy: str | None = None
    ) -> None:
        self._telegram_client = telegram_client
        self.session_name = telegram_client.name
        self.proxy = proxy
        self.start_param = None

    async def _get_telegram_web_data(
        self, peer_id: str, short_name: str, start_param: str | None, attempt: int = 1
    ):
        try:
            if self.proxy:
                proxy = Proxy.from_str(self.proxy)
                self._telegram_client.proxy = {
                    "scheme": proxy.protocol,
                    "hostname": proxy.host,
                    "port": proxy.port,
                    "username": proxy.login,
                    "password": proxy.password,
                }

            if start_param:
                self.start_param = start_param

            if not self._telegram_client.is_connected:
                await self._connect_telegram_client()

            peer = await self._telegram_client.resolve_peer(peer_id=peer_id)
            web_view = await self._telegram_client.invoke(
                RequestAppWebView(
                    peer=peer,  # type: ignore
                    platform="android",
                    app=InputBotAppShortName(bot_id=peer, short_name=short_name),  # type: ignore
                    write_allowed=True,
                    start_param=self.start_param,
                )
            )

            auth_url = self.replace_tg_params(web_view.url)

            telegram_web_data = unquote(
                web_view.url.split("tgWebAppData=")[1].split("&tgWebAppVersion")[0]
            )

            query_params = parse_qs(telegram_web_data)
            user_data = self._get_user_data(query_params)

            if self._telegram_client.is_connected:
                await self._telegram_client.disconnect()

            tg_auth_app_data = {
                "init_data": telegram_web_data,
                "auth_url": auth_url,
                "user_data": user_data,
            }

            return tg_auth_app_data
        except FloodWait as error:
            if attempt <= 3:
                logger.warning(
                    f"{self.session_name} | Rate limit exceeded. Will retry in {error.value} seconds"
                )
                await asyncio.sleep(error.value)  # type: ignore
                return await self._get_telegram_web_data(
                    peer_id, short_name, start_param, attempt + 1
                )
            raise Exception(
                f"{self.session_name} | Error while getting telegram web data"
            )
        except Exception:
            if attempt <= 3:
                logger.warning(
                    f"{self.session_name} | Failed to get telegram web data, retrying in 5 seconds | Attempts: {attempt}"
                )
                await asyncio.sleep(5)
                return await self._get_telegram_web_data(
                    peer_id, short_name, start_param, attempt + 1
                )
            raise Exception(
                f"{self.session_name} | Error while getting telegram web data"
            )

    async def _connect_telegram_client(self):
        try:
            await self._telegram_client.connect()
        except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
            logger.error(f"{self.session_name} | Invalid session")
            raise

    def _get_user_data(self, query_params) -> Dict[str, str]:
        user_data = json.loads(query_params["user"][0])

        parsed_user_data = {}
        parsed_user_data["start_param"] = query_params.get("start_param", [""])[0]
        parsed_user_data["user_id"] = user_data.get("id", None)
        parsed_user_data["language_code"] = user_data.get("language_code", "en")
        parsed_user_data["is_premium_user"] = user_data.get("is_premium_user", False)

        return parsed_user_data

    def replace_tg_params(self, auth_url: str) -> str:
        auth_url = auth_url.split("&tgWebAppVersion")[0]
        auth_url = "&tgWebAppVersion=8.0&tgWebAppPlatform=android&tgWebAppThemeParams=%7B%22bg_color%22%3A%22%23212d3b%22%2C%22section_bg_color%22%3A%22%231d2733%22%2C%22secondary_bg_color%22%3A%22%23151e27%22%2C%22text_color%22%3A%22%23ffffff%22%2C%22hint_color%22%3A%22%237d8b99%22%2C%22link_color%22%3A%22%235eabe1%22%2C%22button_color%22%3A%22%2350a8eb%22%2C%22button_text_color%22%3A%22%23ffffff%22%2C%22header_bg_color%22%3A%22%23242d39%22%2C%22accent_text_color%22%3A%22%2364b5ef%22%2C%22section_header_text_color%22%3A%22%2379c4fc%22%2C%22subtitle_text_color%22%3A%22%237b8790%22%2C%22destructive_text_color%22%3A%22%23ee686f%22%2C%22section_separator_color%22%3A%22%230d1218%22%2C%22bottom_bar_bg_color%22%3A%22%23151e27%22%7D"
        return auth_url
