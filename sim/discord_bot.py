import asyncio
import discord
from dotfiles import load_dotenv
import os

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("BASE_TOKEN_SNIFFER")
STAGING_CHANNEL_ID = int(os.getenv("STAGING_CHANNEL_ID"))


class SimulatedDiscordBot(discord.Client):
    def __init__(self, event_queue):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix="!", intents=intents)
        self.event_queue = event_queue

    async def setup_hook(self):
        self.bg_task = self.loop.create_task(self.process_events())

    async def on_ready(self):
        print(f"Logged in as {self.user}")

    async def process_events(self):
        while True:
            event = self.event_queue.get_event()
            if event:
                event_type, data = event
                if event_type == "new_token":
                    await self.send_token_info(data)
                elif event_type in ["addLiquidityETH", "removeLiquidityETH"]:
                    await self.send_liquidity_event(event_type, data)
            await asyncio.sleep(1)

    async def send_token_info(self, token_info):
        channel = self.get_channel(STAGING_CHANNEL_ID)
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
        channel = self.get_channel(STAGING_CHANNEL_ID)
        if channel:
            embed_color = 0x00FF00 if event_type == "addLiquidityETH" else 0xFF0000
            embed = discord.Embed(
                title=f"{event_type}: {event_data['token'][:10]}", color=embed_color
            )
            embed.add_field(
                name="Amount", value=f"{event_data['amount']:.4f} ETH", inline=True
            )
            embed.add_field(name="To Address", value=event_data["to"], inline=True)
            embed.add_field(name="Deadline", value=event_data["deadline"], inline=True)
            await channel.send(embed=embed)
