import discord
import os
import asyncio
from dotenv import load_dotenv
from token_utils import (
    w3,
    uniswap_factory_contract,
    get_ERC20_token,
    basescan_link,
    get_token_info,
    get_deployer_info,
    dexscreener_link,
)

# Debug flag
DEBUG = False
# Custom start block
# CUSTOM_START_BLOCK = 17739100
CUSTOM_START_BLOCK = None

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("BASE_TOKEN_SNIFFER")
STAGING_CHANNEL_ID = int(os.getenv("STAGING_CHANNEL_ID"))
BASESCAN_API_TOKEN = os.getenv("BASESCAN_API_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True


class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.token_channel_id = STAGING_CHANNEL_ID
        self.bg_task = None

    async def on_ready(self):
        print(f"Logged in as {self.user})")
        print("------")
        self.bg_task = self.loop.create_task(self.monitor_new_pools_background())

    async def monitor_new_pools_background(self):
        while not self.is_closed():
            try:
                events = monitor_new_pools()
                for event in events:
                    await self.send_token_info(event["token_info"])
            except Exception as e:
                print(f"Error in background task: {e}")
            await asyncio.sleep(10)  # Wait for 10 seconds before next check

    async def send_token_info(self, token_info):
        if self.token_channel_id:
            channel = self.get_channel(self.token_channel_id)
            if channel:
                embed = discord.Embed(
                    title=f"New Pair Created: {token_info['name']}", color=0x00FF00
                )
                embed.add_field(name="Symbol", value=token_info["symbol"], inline=True)
                embed.add_field(
                    name="Decimals", value=token_info["decimals"], inline=True
                )
                embed.add_field(
                    name="Total Supply", value=token_info["total_supply"], inline=True
                )
                embed.add_field(
                    name="Deployer Address",
                    value=token_info["deployer_addy"],
                    inline=False,
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


def monitor_new_pools():
    global CUSTOM_START_BLOCK
    try:
        new_latest_block = w3.eth.get_block("latest")["number"]
        if CUSTOM_START_BLOCK is None:
            CUSTOM_START_BLOCK = new_latest_block - 100  # TODO: set to 1 for production
        if new_latest_block > CUSTOM_START_BLOCK:
            if DEBUG:
                print(f"Checking blocks {CUSTOM_START_BLOCK + 1} to {new_latest_block}")
            events = check_new_pools(CUSTOM_START_BLOCK + 1, new_latest_block)
            CUSTOM_START_BLOCK = new_latest_block
            return events
    except Exception as e:
        print(f"An error occurred in monitor_new_pools: {e}")
    return []


def check_new_pools(from_block, to_block):
    events = uniswap_factory_contract.events.PairCreated.get_logs(
        fromBlock=from_block, toBlock=to_block
    )
    processed_events = []
    for event in events:
        try:
            (ERC20_ADDY, BASESCAN_LINK) = get_ERC20_token(event)
            if ERC20_ADDY:
                name, total_supply, decimals, symbol = get_token_info(ERC20_ADDY)
                deployer_addy, deployer_txHash = get_deployer_info(ERC20_ADDY)
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
                processed_events.append({"token_info": token_info})
                print(f"Processed new token: {name}")
        except Exception as e:
            print(f"Error processing event: {e}")
    return processed_events


def print_token_info(token_info):
    print("New token detected:")
    print(f"Name: {token_info['name']}")
    print(f"Symbol: {token_info['symbol']}")
    print(f"Total Supply: {token_info['total_supply']}")
    print(f"Decimals: {token_info['decimals']}")
    print(f"Deployer Address: {token_info['deployer_addy']}")
    print(f"Deployer Transaction: {token_info['deployer_txHash']}")
    print(f"Basescan Deployer URL: {token_info['basescan_deployer_url']}")
    print(f"Basescan Token URL: {token_info['basescan_token_url']}")
    print("---")


if __name__ == "__main__":
    client = MyBot()
    client.run(DISCORD_BOT_TOKEN)
