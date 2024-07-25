import discord
from discord import app_commands
from dotenv import load_dotenv
import os
from web3 import Web3
from datetime import datetime
import asyncio

# Import functions from your token script
from token_utils import (
    w3,
    uniswap_factory_contract,
    get_ERC20_token,
    basescan_link,
    get_token_info,
    get_deployer_info,
)

# Debug flag
DEBUG = False  # Set this to False to disable debug output

# Custom start block
CUSTOM_START_BLOCK = (
    17567736  # Set this to a specific block number, or None to use the latest block
)

# Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
BASESCAN_API_TOKEN = os.getenv("BASESCAN_API_TOKEN")

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True


class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.token_channel_id = (
            1265364948012371979  # Replace with your actual channel ID
        )

    async def on_ready(self):
        print(f"{self.user} has connected to Discord")
        await self.tree.sync()
        print("Synced commands.")

        if DEBUG:
            print(f"Bot is in {len(self.guilds)} guilds:")
            for guild in self.guilds:
                print(f"- {guild.name} (id: {guild.id})")
                print("  Channels:")
                for channel in guild.text_channels:
                    print(f"  - {channel.name} (id: {channel.id})")

        # Try to fetch the specific channel
        try:
            channel = self.get_channel(self.token_channel_id)
            if channel:
                print(f"Successfully found channel: {channel.name}")
                if DEBUG:
                    permissions = channel.permissions_for(channel.guild.me)
                    print(f"Bot permissions in target channel:")
                    print(f"- View Channel: {permissions.view_channel}")
                    print(f"- Send Messages: {permissions.send_messages}")
                    print(f"- Embed Links: {permissions.embed_links}")
            else:
                print(f"Channel with ID {self.token_channel_id} not found")
        except Exception as e:
            print(f"Error finding channel: {e}")

        # Start the monitoring task
        self.loop.create_task(monitor_new_pools(self))

    async def send_token_info(self, token_info):
        if self.token_channel_id:
            channel = self.get_channel(self.token_channel_id)
            if channel:
                permissions = channel.permissions_for(channel.guild.me)
                if permissions.send_messages and permissions.embed_links:
                    embed = discord.Embed(
                        title=f"New Token Added: {token_info['name']}", color=0x00FF00
                    )
                    embed.add_field(
                        name="Symbol", value=token_info["symbol"], inline=True
                    )
                    embed.add_field(
                        name="Decimals", value=token_info["decimals"], inline=True
                    )
                    embed.add_field(
                        name="Total Supply",
                        value=token_info["total_supply"],
                        inline=True,
                    )
                    embed.add_field(
                        name="Deployer Address",
                        value=token_info["deployer_addy"],
                        inline=False,
                    )
                    embed.add_field(
                        name="Deployer Transaction",
                        value=token_info["deployer_txHash"],
                        inline=False,
                    )
                    embed.add_field(
                        name="Basescan Token Link",
                        value=token_info["basescan_token_url"],
                        inline=False,
                    )
                    embed.add_field(
                        name="Basescan Deployer Link",
                        value=token_info["basescan_deployer_url"],
                        inline=False,
                    )

                    try:
                        await channel.send(embed=embed)
                        print(f"Successfully sent token info for {token_info['name']}")
                    except discord.errors.Forbidden:
                        print(
                            f"Failed to send message for {token_info['name']} due to permissions issues."
                        )
                    except Exception as e:
                        print(
                            f"An error occurred while sending token info for {token_info['name']}: {e}"
                        )
                else:
                    print(
                        f"Bot doesn't have permission to send messages or embed links in channel {channel.name}"
                    )
            else:
                print(f"Channel with ID {self.token_channel_id} not found.")
        else:
            print("Token channel ID not set.")


bot = MyBot()


@bot.tree.command(name="hello", description="Says hello!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello! I am a discord bot.")


@bot.tree.command(name="hello-youtube", description="Say hello to youtube :)")
async def hello_youtube(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Like & Subscribe, comment down below, check the link in the description :)"
    )


@bot.tree.command(
    name="latest-block", description="Latest block on the base chain network"
)
async def latest_block(interaction: discord.Interaction):
    latest_block = w3.eth.get_block("latest")
    block_time = latest_block["timestamp"]
    block_time = datetime.utcfromtimestamp(block_time).strftime("%Y-%m-%d %H:%M:%S")
    await interaction.response.send_message(f"Current block time is {block_time}")


@bot.tree.command(name="token-info", description="Display information about a token")
async def token_info(interaction: discord.Interaction, address: str):
    if not Web3.is_address(address):
        await interaction.response.send_message("Invalid Ethereum address.")
        return

    try:
        name, total_supply, decimals, symbol = get_token_info(address)
        deployer_addy, deployer_txHash = get_deployer_info(address)

        token_info = {
            "name": name,
            "total_supply": total_supply,
            "decimals": decimals,
            "symbol": symbol,
            "deployer_addy": deployer_addy,
            "deployer_txHash": deployer_txHash,
            "basescan_deployer_url": basescan_link(deployer_addy),
            "basescan_token_url": basescan_link(address),
        }

        embed = discord.Embed(title=f"Token Information: {name}", color=0x00FF00)
        embed.add_field(name="Symbol", value=symbol, inline=True)
        embed.add_field(name="Decimals", value=decimals, inline=True)
        embed.add_field(name="Total Supply", value=total_supply, inline=True)
        embed.add_field(name="Deployer Address", value=deployer_addy, inline=False)
        embed.add_field(
            name="Deployer Transaction", value=deployer_txHash, inline=False
        )
        embed.add_field(
            name="Basescan Token Link",
            value=token_info["basescan_token_url"],
            inline=False,
        )
        embed.add_field(
            name="Basescan Deployer Link",
            value=token_info["basescan_deployer_url"],
            inline=False,
        )

        await interaction.response.send_message(embed=embed)
    except Exception as e:
        await interaction.response.send_message(
            f"An error occurred while fetching token information: {e}"
        )


async def monitor_new_pools(bot):
    global CUSTOM_START_BLOCK
    latest_block = None

    while True:
        try:
            new_latest_block = w3.eth.get_block("latest")["number"]

            if latest_block is None:
                if CUSTOM_START_BLOCK is not None:
                    latest_block = CUSTOM_START_BLOCK
                    print(f"Starting monitoring from custom block: {latest_block}")
                else:
                    latest_block = new_latest_block - 1
                    print(f"Starting monitoring from latest block: {latest_block}")

            if new_latest_block > latest_block:
                if DEBUG:
                    print(f"Checking blocks {latest_block + 1} to {new_latest_block}")
                events = check_new_pools(latest_block + 1, new_latest_block)
                for event in events:
                    await bot.send_token_info(event["token_info"])
                latest_block = new_latest_block

        except Exception as e:
            print(f"An error occurred in monitor_new_pools: {e}")

        await asyncio.sleep(10)  # Wait for 10 seconds before checking for new blocks


def check_new_pools(from_block, to_block):
    events = uniswap_factory_contract.events.PoolCreated.get_logs(
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
                    "deployer_txHash": deployer_txHash,
                    "basescan_deployer_url": basescan_link(deployer_addy),
                    "basescan_token_url": BASESCAN_LINK,
                }

                processed_events.append({"token_info": token_info})
                print(f"Processed new token: {name}")
        except Exception as e:
            print(f"Error processing event: {e}")

    return processed_events


# Run the bot
bot.run(DISCORD_BOT_TOKEN)
