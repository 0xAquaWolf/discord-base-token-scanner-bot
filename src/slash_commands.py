import discord
from discord import app_commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
STAGING_CHANNEL_ID = int(os.getenv("STAGING_CHANNEL_ID"))
BASESCAN_API_TOKEN = os.getenv("BASESCAN_API_TOKEN")


@app_commands.command(name="hello-youtube", description="Say hello to youtube :)")
async def hello_youtube(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Like & Subscribe, comment down below, check the link in the description :)"
    )


@app_commands.command(
    name="clear-channel", description="Delete all messages in the staging channel"
)
@app_commands.checks.has_permissions(manage_messages=True)
async def clear_channel(interaction: discord.Interaction):
    if interaction.channel_id != STAGING_CHANNEL_ID:
        await interaction.response.send_message(
            "This command can only be used in the staging channel.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    channel = interaction.channel
    deleted = await channel.purge(limit=None)

    print(f"Deleted {len(deleted)} messages from the staging channel.")

    await interaction.followup.send(
        f"Deleted {len(deleted)} messages from the staging channel.", ephemeral=True
    )


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        await self.tree.sync()


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user})")
    print("------")


client.tree.add_command(hello_youtube)
client.tree.add_command(clear_channel)

client.run(DISCORD_BOT_TOKEN)
