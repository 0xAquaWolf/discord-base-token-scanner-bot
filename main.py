import asyncio
from config import load_config
from core.blockchain import BlockchainInterface
from interfaces.discord_bot import DiscordBot
from interfaces.scanner import BlockchainScanner
from logic.command_center import CommandCenter
from utils.logger import setup_logger
from db.database import Database
from core.event_queue import EventQueue

logger = setup_logger(__name__)


async def main():
    config = load_config()
    database = Database(config)
    await database.connect()
    event_queue = EventQueue()
    blockchain = BlockchainInterface(config)
    discord_bot = DiscordBot(config, database)
    scanner = BlockchainScanner(blockchain, database, event_queue, config)
    command_center = CommandCenter(blockchain, database, discord_bot, scanner, config)

    try:
        await asyncio.gather(
            discord_bot.start(config["DISCORD_BOT_TOKEN"]), command_center.start()
        )
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        await discord_bot.close()
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
