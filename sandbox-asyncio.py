"""
TODO: Re-Architech the bot so that it run asyncio with co-routines for every process
TODO: Impliment a process manger that oversees all of the coroutines
TODO: Create a event queue
TODO: Message handler
TODO: Impliment a way to handle error messages and logs
TODO: Figure out how i'm going to configure it so that i can build the core engine and
then swap out any settings without having to rewrite the code

"""

import asyncio
import discord
import random
from dotenv import load_dotenv
import os

load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("BASE_TOKEN_SNIFFER")
STAGING_CHANNEL_ID = int(os.getenv("STAGING_CHANNEL_ID"))


class SimulationBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(commands_prefix="!", intents=intents)
        self.channel_id = STAGING_CHANNEL_ID
        self.bg_task = None

    async def setup_hook(self):
        self.bg_task = self.loop.create_task(self.simulate_blockchain_scanning())

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        print("------------")

    async def simulate_blockchain_scanning(self):
        while not self.is_closed():
            try:
                events = await self.simulate_new_pools()
                for event in events:
                    await self.send_token_info(event)
            except Exception as e:
                print(f"Error in background task: {e}")
            await asyncio.sleep(10)

    async def simulate_new_pools(self):
        # Simulate finding new pools
        await asyncio.sleep(2)  # sim processing time
        if random.random() < 0.3:  # 30% chance
            return [self.generate_fake_token_info()]
        return []

    def generate_fake_token_info(self):
        # Generate fake token information
        random_token = {
            "name": f"Token{random.randint(1000, 9999)}",
            "symbol": f"TKN{random.randint(100, 999)}",
            "total_supply": random.randint(1000000, 1000000000),
            "decimals": random.choice([6, 8, 18]),
            "deployer_address": f"0x{os.urandom(20).hex()}",
            "creation_tx": f"0x{os.urandom(32).hex()}",
        }
        print("This is a random token created")
        print(random_token)
        return random_token

    async def send_token_info(self, token_info):
        channel = self.get_channel(self.channel_id)
        if channel:
            embed = discord.Embed(
                title=f"New Token Detected: {token_info['name']}", color=0x00FF00
            )
            embed.add_field(name="Symbol", value=token_info["symbol"], inline=True)
            embed.add_field(
                name="Supply", value=token_info["total_supply"], inline=True
            )
            embed.add_field(name="Decimals", value=token_info["decimals"], inline=True)
            embed.add_field(
                name="Deployer Address", value=token_info["deployer_address"]
            )
            embed.add_field(name="Creation Tx", value=token_info["creation_tx"])
            await channel.send(embed=embed)

    async def close(self):
        print("Closing bot..")
        if self.bg_task:
            self.bg_task.cancel()
        await super().close()


if __name__ == "__main__":
    bot = SimulationBot()
    try:
        bot.run(DISCORD_BOT_TOKEN)
    except KeyboardInterrupt:
        print("Bot interupted!!! Shutting Down!!!")
    finally:
        asyncio.run(bot.close())
