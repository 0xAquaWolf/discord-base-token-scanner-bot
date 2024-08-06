from web3 import Web3
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BlockchainInterface:
    def __init__(self, config):
        self.w3 = Web3(
            Web3.HTTPProvider("https://mainnet.base.org")
        )  # Adjust URL if needed
        self.config = config

    async def get_latest_block(self):
        try:
            return self.w3.eth.get_block("latest")
        except Exception as e:
            logger.error(f"Error getting latest block: {e}")
            return None

    async def get_block(self, block_number):
        try:
            return self.w3.eth.get_block(block_number, full_transactions=True)
        except Exception as e:
            logger.error(f"Error getting block {block_number}: {e}")
            return None

    # Add other blockchain interaction methods as needed
