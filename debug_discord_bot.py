import discord
import asyncio
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")


class DebugBot(discord.Client):
    def __init__(self, channel_id):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(intents=intents)
        self.channel_id = channel_id

    async def on_ready(self):
        print(f"{self.user} has connected to Discord!")
        print(f"Bot is in {len(self.guilds)} guilds:")

        for guild in self.guilds:
            print(f"- {guild.name} (id: {guild.id})")
            print("  Channels:")
            for channel in guild.text_channels:
                print(f"  - {channel.name} (id: {channel.id})")
                if channel.id == self.channel_id:
                    print(f"    ** This is the target channel **")
                    await self.debug_channel(channel)

        await self.close()

    async def debug_channel(self, channel):
        print(f"Debugging channel: {channel.name}")

        # Check permissions
        permissions = channel.permissions_for(channel.guild.me)
        print(f"Bot permissions in this channel:")
        print(f"- View Channel: {permissions.view_channel}")
        print(f"- Send Messages: {permissions.send_messages}")
        print(f"- Embed Links: {permissions.embed_links}")

        # Try to send a message
        if permissions.send_messages:
            try:
                await channel.send(
                    "Debug message - If you see this, the bot can send messages here!"
                )
                print("Successfully sent a message to the channel.")
            except discord.errors.Forbidden:
                print("Failed to send a message due to permissions issues.")
            except Exception as e:
                print(f"An error occurred while sending a message: {e}")
        else:
            print("Bot does not have permission to send messages in this channel.")


async def main():
    channel_id = 1265364948012371979  # Replace with your channel ID
    bot = DebugBot(channel_id)
    try:
        await bot.start(TOKEN)
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
