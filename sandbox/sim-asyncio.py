"""
- TODO: Bot stops sending messages, need to figure out why this is happening....
- TODO: Save events to the database

 look into check_new_pools range error (out of range)

Look into changing the architecture into something more like this
Scanner script > inserts into psql db then > another listening for write events > output data to discord
"""

import asyncio
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import logging
from collections import deque
from eth_abi import decode
from eth_utils import to_checksum_address
from datetime import datetime

from utils.token_utils import (
    w3,
    uniswap_factory_contract,
    get_ERC20_token,
    basescan_link,
    get_token_info,
    get_deployer_info,
    dexscreener_link,
    print_token_info,
    ERC20_ABI,
    basescan_tx_link,
    uniswap_addys,
)

# Debug mode toggle
DEBUG_MODE = False

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def log(message, level=logging.INFO):
    if DEBUG_MODE or level >= logging.INFO:
        logger.log(level, message)


load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("BASE_TOKEN_SNIFFER")
STAGING_CHANNEL_ID = int(os.getenv("STAGING_CHANNEL_ID"))
BASESCAN_API_TOKEN = os.getenv("BASESCAN_API_TOKEN")

CUSTOM_START_BLOCK = None


class EventQueue:
    def __init__(self):
        self.queue = deque()

    def add_event(self, event):
        self.queue.append(event)

    def get_event(self):
        return self.queue.popleft() if self.queue else None


class MessageHandler:
    def __init__(self, bot):
        self.bot = bot

    async def send_token_info(self, token_info):
        channel = self.bot.get_channel(STAGING_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title=f"New Pair Created: {token_info['name']}", color=0x0000FF
            )
            embed.add_field(name="Symbol", value=token_info["symbol"], inline=True)
            embed.add_field(name="Decimals", value=token_info["decimals"], inline=True)
            embed.add_field(
                name="Total Supply", value=token_info["total_supply"], inline=True
            )
            embed.add_field(
                name="Deployer Address", value=token_info["deployer_addy"], inline=False
            )
            embed.add_field(
                name="Deployer TXHash",
                value=token_info["deployer_txHash"],
                inline=False,
            )
            embed.add_field(
                name="Basescan Token Link",
                value=token_info["basescan_token_url"],
                inline=False,
            )
            embed.add_field(
                name="Dexscreener Token Link",
                value=token_info["dexscreener_url"],
                inline=False,
            )
            embed.add_field(
                name="Basescan Deployer Link",
                value=token_info["basescan_deployer_url"],
                inline=False,
            )
            await channel.send(embed=embed)

    async def send_liquidity_event(self, event_type, event_data):
        channel = self.bot.get_channel(STAGING_CHANNEL_ID)
        if channel:
            embed_color = 0x00FF00 if event_type == "addLiquidityETH" else 0xFF0000

            embed = discord.Embed(
                title=f"{event_type}: {event_data['token_name']}", color=embed_color
            )
            embed.add_field(
                name="Symbol", value=event_data["token_symbol"], inline=True
            )

            if event_type == "addLiquidityETH":
                embed.add_field(
                    name="ETH Amount",
                    value=f"{event_data['eth_amount']:.4f} ETH",
                    inline=True,
                )
                embed.add_field(
                    name="Token Amount",
                    value=f"{event_data['token_amount']:.4f} {event_data['token_symbol']}",
                    inline=True,
                )
            else:  # removeLiquidityETH
                embed.add_field(
                    name="Liquidity",
                    value=f"{event_data['liquidity']:.4f}",
                    inline=True,
                )

            embed.add_field(
                name="Min Token",
                value=f"{event_data['token_min']:.4f} {event_data['token_symbol']}",
                inline=True,
            )
            embed.add_field(
                name="Min ETH", value=f"{event_data['eth_min']:.4f} ETH", inline=True
            )
            embed.add_field(
                name="To Address", value=event_data["to_address"], inline=True
            )
            embed.add_field(
                name="Deadline",
                value=datetime.fromtimestamp(event_data["deadline"]).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                inline=True,
            )
            embed.add_field(
                name="Transaction",
                value=basescan_tx_link(event_data["tx_hash"]),
                inline=False,
            )

            await channel.send(embed=embed)


class ProcessManager:
    def __init__(self, bot, event_queue, uniswap_factory_contract):
        self.bot = bot
        self.event_queue = event_queue
        self.uniswap_factory_contract = uniswap_factory_contract
        self.tasks = []
        self.last_checked_block = None

    def start_tasks(self):
        self.tasks.extend(
            [
                asyncio.create_task(self.monitor_new_pools()),
                asyncio.create_task(self.monitor_liquidity_events()),
                asyncio.create_task(self.process_events()),
            ]
        )

    async def stop_tasks(self):
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def monitor_new_pools(self):
        while True:
            try:
                new_latest_block = await self.bot.loop.run_in_executor(
                    None, w3.eth.get_block, "latest"
                )
                new_latest_block = new_latest_block["number"]
                if self.last_checked_block is None:
                    self.last_checked_block = (
                        new_latest_block - 1
                    )  # Set to 1 for production
                if new_latest_block > self.last_checked_block - 1:
                    events = await self.check_new_pools(
                        self.last_checked_block + 1, new_latest_block + 1
                    )
                    for event in events:
                        self.event_queue.add_event(("new_token", event["token_info"]))
            except Exception as e:
                logger.error(f"Error in monitor_new_pools: {e}")
            await asyncio.sleep(10)

    async def check_new_pools(self, from_block, to_block):
        try:
            events = await self.bot.loop.run_in_executor(
                None,
                lambda: uniswap_factory_contract.events.PairCreated.get_logs(
                    fromBlock=from_block, toBlock=to_block
                ),
            )
            processed_events = []
            for event in events:
                try:
                    ERC20_ADDY, BASESCAN_LINK = await self.bot.loop.run_in_executor(
                        None, get_ERC20_token, event
                    )
                    if ERC20_ADDY:
                        token_info = await self.get_token_info(
                            ERC20_ADDY, BASESCAN_LINK
                        )
                        processed_events.append({"token_info": token_info})
                        logger.info(f"Processed new token: {token_info['name']}")
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
            return processed_events
        except Exception as e:
            logger.error(f"Error in check_new_pools: {e}")
            return []

    async def get_token_info(self, ERC20_ADDY, BASESCAN_LINK):
        name, total_supply, decimals, symbol = await self.bot.loop.run_in_executor(
            None, get_token_info, ERC20_ADDY
        )
        deployer_addy, deployer_txHash = await self.bot.loop.run_in_executor(
            None, get_deployer_info, ERC20_ADDY
        )
        token_info = {
            "name": name,
            "total_supply": total_supply,
            "decimals": decimals,
            "symbol": symbol,
            "deployer_addy": deployer_addy,
            "deployer_txHash": f"https://basescan.org/tx/{deployer_txHash}",
            "basescan_deployer_url": basescan_link(deployer_addy),
            "basescan_token_url": BASESCAN_LINK,
            "dexscreener_url": dexscreener_link(ERC20_ADDY),
        }
        print_token_info(token_info)
        return token_info

    async def monitor_liquidity_events(self):
        add_liquidity_eth_selector = w3.keccak(
            text="addLiquidityETH(address,uint256,uint256,uint256,address,uint256)"
        ).hex()[:10]
        add_liquidity_eth_selector_bytes = bytes.fromhex(add_liquidity_eth_selector[2:])

        remove_liquidity_eth_selector = w3.keccak(
            text="removeLiquidityETH(address,uint256,uint256,uint256,address,uint256)"
        ).hex()[:10]
        remove_liquidity_eth_selector_bytes = bytes.fromhex(
            remove_liquidity_eth_selector[2:]
        )

        while True:
            try:
                new_latest_block = await self.bot.loop.run_in_executor(
                    None, w3.eth.get_block, "latest", True
                )
                new_latest_block_number = new_latest_block["number"]

                if self.last_checked_block is None:
                    self.last_checked_block = new_latest_block_number - 100

                if new_latest_block_number > self.last_checked_block:
                    for block_number in range(
                        self.last_checked_block + 1, new_latest_block_number + 1
                    ):
                        block = await self.bot.loop.run_in_executor(
                            None, w3.eth.get_block, block_number, True
                        )
                        for tx in block.transactions:
                            if tx["to"] == uniswap_addys["UniswapV2Router"]:
                                input_data = tx["input"]
                                if input_data.startswith(
                                    add_liquidity_eth_selector_bytes
                                ):
                                    await self.process_add_liquidity_eth_event(tx)
                                elif input_data.startswith(
                                    remove_liquidity_eth_selector_bytes
                                ):
                                    await self.process_remove_liquidity_eth_event(tx)

                    self.last_checked_block = new_latest_block_number

            except Exception as e:
                logger.error(f"Error in monitor_liquidity_events: {e}")

            await asyncio.sleep(10)

    async def process_remove_liquidity_eth_event(self, tx):
        try:
            tx_hash = tx["hash"].hex()

            # Decode the input data
            input_data = tx["input"]
            data = input_data.hex()[10:]

            # Define the types of the function parameters
            param_types = [
                "address",
                "uint256",
                "uint256",
                "uint256",
                "address",
                "uint256",
            ]

            # Decode the input data
            decoded = decode(param_types, bytes.fromhex(data))

            token_address = to_checksum_address(decoded[0])
            liquidity = decoded[1]
            amount_token_min = decoded[2]
            amount_eth_min = decoded[3]
            to_address = to_checksum_address(decoded[4])
            deadline = decoded[5]

            token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)

            token_name = await self.bot.loop.run_in_executor(
                None, token_contract.functions.name().call
            )
            token_symbol = await self.bot.loop.run_in_executor(
                None, token_contract.functions.symbol().call
            )
            token_decimals = await self.bot.loop.run_in_executor(
                None, token_contract.functions.decimals().call
            )

            event_data = {
                "event_type": "removeLiquidityETH",
                "token_name": token_name,
                "token_symbol": token_symbol,
                "token_decimals": token_decimals,
                "liquidity": w3.from_wei(liquidity, "ether"),
                "token_min": w3.from_wei(amount_token_min, "ether"),
                "eth_min": w3.from_wei(amount_eth_min, "ether"),
                "to_address": to_address,
                "deadline": deadline,
                "tx_hash": tx_hash,
            }

            self.event_queue.add_event(("removeLiquidityETH", event_data))
            logger.info(f"Processed removeLiquidityETH event: {event_data}")

        except Exception as e:
            logger.error(
                f"Error processing removeLiquidityETH event: {e}", exc_info=True
            )

    async def process_add_liquidity_eth_event(self, tx):
        try:
            tx_hash = tx["hash"].hex()

            # Decode the input data
            input_data = tx["input"]
            data = input_data.hex()[10:]

            # Define the types of the function parameters
            param_types = [
                "address",
                "uint256",
                "uint256",
                "uint256",
                "address",
                "uint256",
            ]

            # Decode the input data
            decoded = decode(param_types, bytes.fromhex(data))

            # Function signature
            # function_signature = "addLiquidityETH(address token, uint256 amountTokenDesired, uint256 amountTokenMin, uint256 amountETHMin, address to, uint256 deadline)"

            token_address = to_checksum_address(decoded[0])
            amount_token_desired = decoded[1]
            amount_token_min = decoded[2]
            amount_eth_min = decoded[3]
            to_address = to_checksum_address(decoded[4])
            deadline = decoded[5]

            eth_amount = tx["value"]

            token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)

            token_name = await self.bot.loop.run_in_executor(
                None, token_contract.functions.name().call
            )
            token_symbol = await self.bot.loop.run_in_executor(
                None, token_contract.functions.symbol().call
            )
            token_decimals = await self.bot.loop.run_in_executor(
                None, token_contract.functions.decimals().call
            )

            # receipt = await self.bot.loop.run_in_executor(
            #     None, w3.eth.get_transaction_receipt, tx["hash"]
            # )

            # Placeholder for LP tokens, you'll need to extract this from the logs
            lp_tokens = "N/A"

            event_data = {
                "event_type": "addLiquidityETH",
                "token_name": token_name,
                "token_symbol": token_symbol,
                "token_decimals": token_decimals,
                "eth_amount": w3.from_wei(eth_amount, "ether"),
                "token_amount": w3.from_wei(amount_token_desired, "ether"),
                "token_min": w3.from_wei(amount_token_min, "ether"),
                "eth_min": w3.from_wei(amount_eth_min, "ether"),
                "to_address": to_address,
                "deadline": deadline,
                "lp_tokens": lp_tokens,
                "tx_hash": tx_hash,
            }

            self.event_queue.add_event(("addLiquidityETH", event_data))
            logger.info(f"Processed addLiquidityETH event: {event_data}")

        except Exception as e:
            logger.error(f"Error processing addLiquidityETH event: {e}", exc_info=True)

    async def process_events(self):
        message_handler = MessageHandler(self.bot)
        while True:
            event = self.event_queue.get_event()
            if event:
                event_type, data = event
                if event_type == "new_token":
                    await message_handler.send_token_info(data)
                elif event_type in ["addLiquidityETH", "removeLiquidityETH"]:
                    await message_handler.send_liquidity_event(event_type, data)
            await asyncio.sleep(1)


class TokenMonitorBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
        self.event_queue = EventQueue()
        self.process_manager = ProcessManager(
            self, self.event_queue, uniswap_factory_contract
        )

    async def setup_hook(self):
        self.process_manager.start_tasks()

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")

    async def close(self):
        logger.info("Closing bot...")
        await self.process_manager.stop_tasks()
        await super().close()


if __name__ == "__main__":
    load_dotenv()
    DISCORD_BOT_TOKEN = os.getenv("BASE_TOKEN_SNIFFER")
    STAGING_CHANNEL_ID = int(os.getenv("STAGING_CHANNEL_ID"))
    BASESCAN_API_TOKEN = os.getenv("BASESCAN_API_TOKEN")

    bot = TokenMonitorBot()
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot interrupted! Shutting down...")
    finally:
        asyncio.run(bot.close())
