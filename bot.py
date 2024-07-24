import discord
from discord import app_commands
from dotenv import load_dotenv
import os
from web3 import Web3
from datetime import datetime

rpc_url = "https://mainnet.base.org"
web3 = Web3(Web3.HTTPProvider(rpc_url))

if web3.is_connected():
    print("Connected to Base chain network")
else:
    print("Failed to connect to the Base chain node")

# Load environment variables from .env file
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# Set up bot intents
intents = discord.Intents.default()
intents.message_content = True

latest_block = web3.eth.get_block("latest")
block_time = latest_block["timestamp"]
block_time = datetime.utcfromtimestamp(block_time).strftime("%Y-%m-%d %H:%M:%S")
print(f"Current Block time {block_time}")


class MyBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f"{self.user} has connected to Discord")
        # Sync the commands with Discord
        await self.tree.sync()


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
    name="latest-block", description="latest block on the base chain network"
)
async def latest_block(interaction: discord.Interaction):
    latest_block = web3.eth.get_block("latest")
    block_time = latest_block["timestamp"]
    block_time = datetime.utcfromtimestamp(block_time).strftime("%Y-%m-%d %H:%M:%S")
    print(block_time)
    await interaction.response.send_message(f"current block time is {block_time}")


bot.run(DISCORD_BOT_TOKEN)
