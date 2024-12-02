import asyncio
from time import time
from typing import Any
import zstandard as zstd
import cloudscraper
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from bot.config import settings

from bot.utils import logger
from bot.exceptions import InvalidSession
from .agents import get_sec_ch_ua
from .headers import headers

from random import randint, random
from ..utils.graphql import Query, OperationName
from ..utils.tg_manager.TGSession import TGSession


class Tapper:
    def __init__(self, tg_session: TGSession):
        self.tg_session = tg_session
        self.session_name = tg_session.session_name
        self.balance = 0

    def make_request(self, http_client: cloudscraper.CloudScraper, operation_name: str, query: str, variables: Any):
        payload = \
            {
                'operationName': operation_name,
                'query': query,
                'variables': variables
            }
        response = http_client.post(f'https://api.goblinmine.game/graphql', json=payload, timeout=60)
        return response

    async def login(self, http_client: cloudscraper.CloudScraper, tg_web_data: str, retry=0):
        try:
            response = self.make_request(http_client, OperationName.Login, Query.Login,
                                         {'input': {'initData': tg_web_data}})
            response.raise_for_status()
            response_json = response.json()
            auth_token = None
            if response_json['data']['login'].get('status', '') == 'ok':
                auth_token = response_json['data']['login'].get('token')
            return auth_token

        except Exception as error:
            if retry < 3:
                retry += 1
                await asyncio.sleep(delay=randint(15, 25) * retry)
                return await self.login(http_client, tg_web_data=tg_web_data, retry=retry)

            logger.error(f"{self.session_name} | Unknown error when logging: {error}")
            await asyncio.sleep(delay=randint(3, 7))
            return None

    async def check_proxy(self, http_client: cloudscraper.CloudScraper, proxy: str) -> None:
        try:
            response = http_client.get(url='https://ipinfo.io/ip', timeout=20)
            ip = response.text
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def get_worlds(self, http_client: cloudscraper.CloudScraper):
        try:
            response = self.make_request(http_client, OperationName.Worlds, Query.Worlds,
                                         {})
            response.raise_for_status()
            response_json = response.json()
            return response_json['data']['worlds']

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while getting worlds | Error: {e}")
            await asyncio.sleep(delay=3)

    async def get_mines_and_tasks(self, http_client: cloudscraper.CloudScraper, world_id: int):
        try:
            response = self.make_request(http_client, OperationName.MinesAndCheckTasksCompleted,
                                         Query.MinesAndCheckTasksCompleted, {"worldId": world_id})
            response.raise_for_status()
            response_json = response.json()
            return response_json['data']['mines']

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while getting mines data | Error: {e}")
            await asyncio.sleep(delay=3)

    async def claim_mining_reward(self, http_client: cloudscraper.CloudScraper, world_id: int, mine_id: int):
        try:
            response = self.make_request(http_client, OperationName.PickUp,
                                         Query.PickUp, {"input": {"mineId": mine_id, "worldId": world_id}})
            response.raise_for_status()
            await self.get_mines_and_tasks(http_client, world_id)
            return True

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while claim mining reward | Error: {e}")
            await asyncio.sleep(delay=3)
            return False

    async def buy_mine(self, http_client: cloudscraper.CloudScraper, mine_id: int):
        try:
            response = self.make_request(http_client, OperationName.BuyMine,
                                         Query.BuyMine, {"input": {"mineId": mine_id}})
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while buying new mine | Error: {e}")
            await asyncio.sleep(delay=3)
            return False

    async def buy_miner_level(self, http_client: cloudscraper.CloudScraper, miner_level_id: int):
        try:
            response = self.make_request(http_client, OperationName.BuyMinerLevel,
                                         Query.BuyMinerLevel, {"input": {"minerLevelId": miner_level_id}})
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while buying new miner level | Error: {e}")
            await asyncio.sleep(delay=3)
            return False

    async def buy_miner_slot(self, http_client: cloudscraper.CloudScraper, miner_slot_id: int):
        try:
            response = self.make_request(http_client, OperationName.BuyMiner,
                                         Query.BuyMiner, {"input": {"minerId": miner_slot_id}})
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while buying new miner slot | Error: {e}")
            await asyncio.sleep(delay=3)
            return False

    async def buy_item_inventory(self, http_client: cloudscraper.CloudScraper, item_id: int):
        try:
            response = self.make_request(http_client, OperationName.BuyInventory,
                                         Query.BuyInventory, {"id": item_id})
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while buying item | Error: {e}")
            await asyncio.sleep(delay=3)
            return False

    async def buy_cart(self, http_client: cloudscraper.CloudScraper, cart_id: int):
        try:
            response = self.make_request(http_client, OperationName.UpdateCart,
                                         Query.UpdateCart, {"id": cart_id})
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while buying cart | Error: {e}")
            await asyncio.sleep(delay=3)
            return False

    async def buy_mine_upgrade(self, http_client: cloudscraper.CloudScraper, upgrade_id: int):
        try:
            response = self.make_request(http_client, OperationName.BuyUpgradeMine,
                                         Query.BuyUpgradeMine, {"id": upgrade_id})
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while buying mine upgrade | Error: {e}")
            await asyncio.sleep(delay=3)
            return False

    async def get_expedition(self, http_client: cloudscraper.CloudScraper, expedition_id: int):
        try:
            response = self.make_request(http_client, OperationName.Expedition,
                                         Query.Expedition, {"Id": expedition_id})
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while getting expedition | Error: {e}")
            await asyncio.sleep(delay=3)
            return False

    async def buy_expedition(self, http_client: cloudscraper.CloudScraper, expedition_id: int, amount: int):
        try:
            response = self.make_request(http_client, OperationName.BuyExpedition,
                                         Query.BuyExpedition, {"id": expedition_id, "amount": amount})
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while buying expedition | Error: {e}")
            await asyncio.sleep(delay=3)
            return False

    async def try_upgrade_miners(self, http_client: cloudscraper.CloudScraper, mine_id: int):
        try:
            response = self.make_request(http_client, OperationName.MineAndMiners,
                                         Query.MineAndMiners, {"mineId": mine_id})
            response.raise_for_status()
            response_json = response.json()
            miners = response_json['data']['miners']
            for slot in miners:
                if slot['available']:
                    for miner in slot['minerLevel']:
                        if miner['available'] or miner['price'] > self.balance:
                            continue
                        if miner.get('inventoryLevel', None) is None or miner['existInventoryLevel']:
                            result = await self.buy_miner_level(http_client, miner['id'])
                            if result:
                                self.balance -= miner['price']
                                logger.success(f'{self.session_name} '
                                               f'| Successfully bought miner: <lc>{miner["id"]}</lc> '
                                               f'| Income per hour: <g>{miner["income_hour"]}</g> '
                                               f'| Spent: <fg #08a384>{miner["price"]}</fg #08a384>')

                            await asyncio.sleep(delay=randint(3, 10))

                elif self.balance >= slot['price']:
                    result = await self.buy_miner_slot(http_client, slot['id'])
                    if result:
                        self.balance -= slot['price']
                        logger.success(f'{self.session_name} | Successfully bought a new miner slot '
                                       f'| Name: <lc>{slot["name"]}</lc> '
                                       f'| Spent: <fg #08a384>{slot["price"]}</fg #08a384>')
                    break

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while upgrading miners | Error: {e}")
            await asyncio.sleep(delay=3)

    async def try_upgrade_inventory(self, http_client: cloudscraper.CloudScraper, mine_id: int):
        try:
            response = self.make_request(http_client, OperationName.Inventory,
                                         Query.Inventory, {"mineId": mine_id})
            response.raise_for_status()
            response_json = response.json()
            inventory = response_json['data']['inventory']
            available_items = [item for item in inventory if
                               not item['disabled'] and item.get('price', None) is not None]
            sorted_items = sorted(available_items, key=lambda x: x['income_hour'] / x['price'], reverse=True)
            for item in sorted_items:
                if item['price'] > self.balance:
                    continue

                result = await self.buy_item_inventory(http_client, item['id'])
                if result:
                    self.balance -= item['price']
                    logger.success(f'{self.session_name} '
                                   f'| Successfully upgraded item: <fg #b207b8>{item["name"]}</fg #b207b8> '
                                   f'| Income per hour: <g>+{item["income_hour"]}</g> '
                                   f'| Spent: <fg #08a384>{item["price"]}</fg #08a384>')

                await asyncio.sleep(delay=randint(2, 8))

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while trying to upgrade inventory | Error: {e}")
            await asyncio.sleep(delay=3)

    async def try_upgrade_cart(self, http_client: cloudscraper.CloudScraper, mine_id: int, user_mine_id: int):
        try:
            response = self.make_request(http_client, OperationName.Carts,
                                         Query.Carts, {"mineId": mine_id, "userMineId": user_mine_id})
            response.raise_for_status()
            response_json = response.json()
            carts = response_json['data']['carts']
            sorted_carts = sorted(carts, key=lambda x: x['level'])
            for cart in sorted_carts:
                if not cart['available'] and cart['level'] <= settings.MAX_CART_LEVEL:
                    if cart['price'] > self.balance:
                        continue
                    result = await self.buy_cart(http_client, cart['id'])
                    if result:
                        self.balance -= cart['price']
                        logger.success(f'{self.session_name} | Successfully upgraded cart! '
                                       f'| Cart level: <lc>{cart["level"]}</lc> '
                                       f'| Volume: <fg #8607b8>{cart["volume"]}</fg #8607b8> '
                                       f'| Spent: <fg #08a384>{cart["price"]}</fg #08a384>')

                    await asyncio.sleep(delay=randint(2, 8))
                    break

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while trying to buy cart | Error: {e}")
            await asyncio.sleep(delay=3)

    async def try_upgrade_mine(self, http_client: cloudscraper.CloudScraper, mine_id: int):
        try:
            response = self.make_request(http_client, OperationName.MineAndUpgradeMine,
                                         Query.MineAndUpgradeMine, {"mineId": mine_id})
            response.raise_for_status()
            response_json = response.json()
            mine_upgrades = response_json['data']['upgradeMine']
            active_upgrades = [u for u in mine_upgrades if not u['disabled'] and u.get('price', None) is not None]
            sorted_items = sorted(active_upgrades, key=lambda x: x['deposit_day'] / x['price'], reverse=True)
            for item in sorted_items:
                if item['price'] > self.balance:
                    continue

                if item.get('need_inventory', None) is None:
                    result = await self.buy_mine_upgrade(http_client, item['id'])
                    if result:
                        self.balance -= item['price']
                        logger.success(f'{self.session_name} | Successfully upgraded mine item: '
                                       f'<fg #b207b8>{item["name"]}</fg #b207b8> '
                                       f'| Deposit per day: <e>+{item["deposit_day"]}</e> '
                                       f'| Spent: <fg #08a384>{item["price"]}</fg #08a384>')
                    break

                await asyncio.sleep(delay=randint(2, 8))

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while trying to upgrade mine | Error: {e}")
            await asyncio.sleep(delay=3)

    async def try_send_expeditions(self, http_client: cloudscraper.CloudScraper, world_id: int):
        try:
            response = self.make_request(http_client, OperationName.ExpeditionsAndUserExpeditions,
                                         Query.ExpeditionsAndUserExpeditions, {"worldId": world_id})
            response.raise_for_status()
            response_json = response.json()
            expeditions = response_json['data']['expeditions']
            user_expeditions = response_json['data']['userExpeditions']
            running_expeditions = [ex['name'] for ex in user_expeditions if ex['status'] == 'in_process']
            for expedition in expeditions:
                if expedition['name'] not in running_expeditions and expedition['duration'] >= settings.MIN_EXP_DURATION:
                    expedition_cost = max(settings.CUSTOM_EXPEDITION_COST, expedition['min'])
                    if expedition_cost > self.balance:
                        continue
                    result = await self.get_expedition(http_client, expedition['id'])
                    if result:
                        await asyncio.sleep(delay=randint(1, 5))
                        result = await self.buy_expedition(http_client, expedition['id'], expedition_cost)
                        if result:
                            self.balance -= expedition_cost
                            logger.success(f'{self.session_name} | Successfully sent expedition: {expedition["name"]} '
                                           f'| Spent: <fg #08a384>{expedition_cost}</fg #08a384>')

                    await asyncio.sleep(delay=randint(3, 15))

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while trying to send expeditions | Error: {e}")
            await asyncio.sleep(delay=3)

    async def run(self, user_agent: str, proxy: str | None) -> None:
        access_token_created_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None
        headers["User-Agent"] = user_agent
        headers['Sec-Ch-Ua'] = get_sec_ch_ua(user_agent)
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn, trust_env=True,
                                        auto_decompress=False)
        scraper = cloudscraper.create_scraper()
        if proxy:
            proxies = {
                'http': proxy,
                'https': proxy,
                'socks5': proxy
            }
            scraper.proxies.update(proxies)
            await self.check_proxy(http_client=scraper, proxy=proxy)

        token_live_time = 3600
        scraper.headers = http_client.headers.copy()
        while True:
            try:
                sleep_time = randint(settings.SLEEP_TIME[0], settings.SLEEP_TIME[1])
                if time() - access_token_created_time >= token_live_time:
                    tg_web_data = await self.tg_session.get_tg_web_data()
                    if tg_web_data is None:
                        await asyncio.sleep(randint(100, 180))
                        continue

                    auth_token = await self.login(http_client=scraper, tg_web_data=tg_web_data)
                    if auth_token is None:
                        token_live_time = 0
                        logger.warning(f'{self.session_name} | Failed to login | '
                                       f'Next try after <y>{round(sleep_time / 60, 1)}</y> min')
                        await asyncio.sleep(sleep_time)
                        continue

                    access_token_created_time = time()
                    token_live_time = 3600

                    http_client.headers['Authorization'] = f'Bearer {auth_token}'
                    scraper.headers = http_client.headers.copy()

                    worlds = await self.get_worlds(http_client=scraper)
                    current_world = [world for world in worlds if world['active']][0]
                    balance = current_world['currency']['amount']
                    self.balance = balance
                    logger.info(
                        f"{self.session_name} | Current world: <fg #fc9d03>{current_world['name']}</fg #fc9d03> "
                        f"| Balance: <e>{round(balance, 1)}</e> | Income per hour: <lc>{current_world['income_day']}</lc>")

                    mines_data = await self.get_mines_and_tasks(http_client=scraper, world_id=current_world['id'])

                    if settings.AUTO_MINING:
                        await asyncio.sleep(delay=randint(5, 15))
                        for mine_data in mines_data:
                            if mine_data.get('userMine', None) is not None:
                                reward = round(mine_data['userMine']['extracted_amount'], 1)
                                if reward > 1:
                                    result = await self.claim_mining_reward(http_client=scraper,
                                                                            world_id=current_world['id'],
                                                                            mine_id=mine_data['userMine']['id'])
                                    if result:
                                        self.balance += reward
                                        logger.success(f'{self.session_name} | Successfully claimed mining reward from '
                                                       f'<y>{mine_data["name"]}</y> | Reward: <e>{reward}</e>')
                                    await asyncio.sleep(delay=randint(3, 10))

                    if settings.AUTO_BUY_MINE:
                        await asyncio.sleep(delay=randint(3, 10))
                        for mine_data in mines_data:
                            if mine_data.get('userMine', None) is None and self.balance >= mine_data['price']:
                                result = await self.buy_mine(http_client=scraper, mine_id=mine_data['id'])
                                if result:
                                    logger.success(f'{self.session_name} | New mine purchased: <y>{mine_data["name"]}'
                                                   f'</y> | Spent: <fg #08a384>{mine_data["price"]}</fg #08a384>')
                                    self.balance -= mine_data['price']

                    if settings.AUTO_UPGRADE:
                        for mine_data in mines_data:
                            user_mine = mine_data.get('userMine', None)
                            if user_mine is not None:
                                await asyncio.sleep(delay=randint(3, 10))
                                max_miners = mine_data['miner_amount']
                                user_miners = mine_data['user_miners_count']
                                max_dep = user_mine['deposit_day_default']
                                current_dep = round(user_mine['deposit_day'], 1)
                                cart_volume = user_mine['volume']
                                logger.info(f'{self.session_name} | Current mine: <y>{mine_data["name"]}</y> | '
                                            f'Deposits per day: <g>{current_dep}/{max_dep}</g> | '
                                            f'Miners: <fg #b8072e>{user_miners}/{max_miners}</fg #b8072e> | '
                                            f'Cart volume: <fg #8607b8>{cart_volume}</fg #8607b8>')

                                if settings.UPGRADE_MINE and user_mine['extracted_percent'] > 70:
                                    await self.try_upgrade_mine(http_client=scraper, mine_id=mine_data['id'])
                                if settings.UPGRADE_MINERS:
                                    await self.try_upgrade_miners(http_client=scraper, mine_id=mine_data['id'])
                                if settings.UPGRADE_INVENTORY:
                                    await self.try_upgrade_inventory(http_client=scraper, mine_id=mine_data['id'])
                                if settings.UPGRADE_CART:
                                    await self.try_upgrade_cart(http_client=scraper, mine_id=mine_data['id'],
                                                                user_mine_id=user_mine['id'])

                    if settings.EXPEDITIONS:
                        await asyncio.sleep(delay=randint(3, 10))
                        await self.try_send_expeditions(http_client=scraper, world_id=current_world['id'])

                logger.info(f"{self.session_name} | Sleep <y>{round(sleep_time / 60, 1)}</y> min")
                await asyncio.sleep(delay=sleep_time)

            except InvalidSession as error:
                raise error

            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=randint(60, 120))

            except KeyboardInterrupt:
                logger.warning("<r>Bot stopped by user...</r>")
            finally:
                if scraper is not None:
                    await http_client.close()
                    scraper.close()


async def run_tapper(tg_session: TGSession, user_agent: str, proxy: str | None):
    try:
        await Tapper(tg_session=tg_session).run(user_agent=user_agent, proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_session.session_name} | Invalid Session")
