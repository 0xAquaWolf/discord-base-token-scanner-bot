import asyncio
from utils.logger import setup_logger
from interfaces.scanner import BlockchainScanner
from interfaces.discord_bot import DiscordBot
from db.database import Database
from core.blockchain import BlockchainInterface

logger = setup_logger(__name__)


class CommandCenter:
    def __init__(
        self,
        blockchain: BlockchainInterface,
        database: Database,
        discord_bot: DiscordBot,
        scanner: BlockchainScanner,
        config,
    ):
        self.blockchain = blockchain
        self.database = database
        self.discord_bot = discord_bot
        self.scanner = scanner
        self.config = config

    async def start(self):
        logger.info("Command Center starting...")
        await asyncio.gather(
            self.scanner.start_monitoring(), self.discord_bot.start_bot()
        )

    async def process_new_token(self, token_info):
        try:
            await self.database.insert_new_token(token_info)
            logger.info(f"New token processed and saved: {token_info['name']}")
        except Exception as e:
            logger.error(f"Error processing new token: {e}", exc_info=True)

    async def process_liquidity_event(self, event_type, event_data):
        try:
            await self.database.insert_liquidity_event(event_type, event_data)
            logger.info(
                f"Liquidity event processed and saved: {event_type} for {event_data['token_name']}"
            )
        except Exception as e:
            logger.error(f"Error processing liquidity event: {e}", exc_info=True)

    async def update_token_price(self, token_address):
        try:
            price = await self.blockchain.get_token_price(token_address)
            await self.database.update_token_price(token_address, price)
            logger.info(f"Updated price for token {token_address}: {price}")
        except Exception as e:
            logger.error(f"Error updating token price: {e}", exc_info=True)

    async def check_token_activity(self, token_address):
        try:
            activity = await self.blockchain.get_token_activity(token_address)
            await self.database.update_token_activity(token_address, activity)
            logger.info(f"Updated activity for token {token_address}")
        except Exception as e:
            logger.error(f"Error checking token activity: {e}", exc_info=True)

    async def analyze_market_trends(self):
        try:
            trends = await self.blockchain.analyze_market_trends()
            await self.database.save_market_trends(trends)
            logger.info("Market trends analyzed and saved")
        except Exception as e:
            logger.error(f"Error analyzing market trends: {e}", exc_info=True)

    async def handle_user_command(self, command, *args):
        try:
            if command == "price":
                token_address = args[0]
                price = await self.blockchain.get_token_price(token_address)
                return f"The current price of the token at {token_address} is {price}"
            elif command == "activity":
                token_address = args[0]
                activity = await self.blockchain.get_token_activity(token_address)
                return f"Recent activity for token at {token_address}: {activity}"
            elif command == "trends":
                trends = await self.blockchain.analyze_market_trends()
                return f"Current market trends: {trends}"
            else:
                return "Unknown command"
        except Exception as e:
            logger.error(f"Error handling user command: {e}", exc_info=True)
            return "An error occurred while processing your command"

    async def periodic_tasks(self):
        while True:
            await self.analyze_market_trends()
            await asyncio.sleep(3600)  # Run every hour

    async def run(self):
        await asyncio.gather(self.start(), self.periodic_tasks())
