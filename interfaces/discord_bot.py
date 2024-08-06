import discord
from discord.ext import commands
import asyncio
from datetime import datetime
from utils.logger import setup_logger
from utils.token_utils import basescan_tx_link
import asyncpg
import json
from db.database import Database

logger = setup_logger(__name__)


class DiscordBot(commands.Bot):
    def __init__(self, config, database: Database):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        self.database = database
        super().__init__(command_prefix="!", intents=intents)
        self.config = config
        self.staging_channel_id = config["STAGING_CHANNEL_ID"]

    async def setup_hook(self):
        logger.info("Bot is setting up...")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user}")
        self.bg_task = self.loop.create_task(self.listen_for_db_events())

    async def listen_for_db_events(self):
        try:
            conn = await asyncpg.connect(
                host=self.config["DB_HOST"],
                port=self.config["DB_PORT"],
                user=self.config["DB_USER"],
                password=self.config["DB_PASSWORD"],
                database=self.config["DB_NAME"],
            )
            await conn.add_listener("new_token", self.on_new_token)
            await conn.add_listener("liquidity_event", self.on_liquidity_event)
            while not self.is_closed():
                print("db connection >> ", conn)
                print(self)
                await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Error in database listener: {e}")
        finally:
            await conn.close()

    async def on_new_token(self, connection, pid, channel, payload):
        token_info = json.loads(payload)
        await self.send_token_info(token_info)

    async def on_liquidity_event(self, connection, pid, channel, payload):
        event_data = json.loads(payload)
        await self.send_liquidity_event(event_data["event_type"], event_data)

    async def send_token_info(self, token_info):
        channel = self.get_channel(self.staging_channel_id)
        if channel:
            try:
                embed = discord.Embed(
                    title=f"New Pair Created: {token_info['name']}", color=0x0000FF
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
                logger.info(f"Sent token info for {token_info['name']} to Discord")
            except Exception as e:
                logger.error(f"Error sending token info to Discord: {e}", exc_info=True)
        else:
            logger.error(f"Channel with ID {self.staging_channel_id} not found")

    async def send_liquidity_event(self, event_type, event_data):
        channel = self.get_channel(self.staging_channel_id)
        if channel:
            try:
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
                    name="Min ETH",
                    value=f"{event_data['eth_min']:.4f} ETH",
                    inline=True,
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
                logger.info(
                    f"Sent {event_type} event for {event_data['token_name']} to Discord"
                )
            except Exception as e:
                logger.error(
                    f"Error sending liquidity event to Discord: {e}", exc_info=True
                )
        else:
            logger.error(f"Channel with ID {self.staging_channel_id} not found")

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith("!help"):
            await message.channel.send(
                "Available commands:\n!help - Show this help message"
            )

        # Process commands
        await self.process_commands(message)

    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send("Pong!")

    # Add more commands as needed

    async def start_bot(self):
        try:
            await self.start(self.config["DISCORD_BOT_TOKEN"])
        except Exception as e:
            logger.error(f"Error starting Discord bot: {e}", exc_info=True)
        finally:
            if not self.is_closed():
                await self.close()
