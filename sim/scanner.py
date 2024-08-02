import asyncio
from simulated_blockchain import SimulatedBlockchain
import json
import random
from eth_util import to_checksum_address


class SimulatedScanner:
    def __init__(self, event_queue):
        self.blockchain = SimulatedBlockchain()
        self.event_queue = event_queue
        self.last_checked_block = 0

    async def scan(self):
        while True:
            latest_block = self.blockchain.get_latest_block()
            if latest_block > self.last_checked_block:
                for block in range(self.last_checked_block + 1, latest_block + 1):
                    event = self.blockchain.generate_event()
                    await self.process_event(event)
                self.last_checked_block = latest_block
            await asyncio.sleep(1)

    async def process_event(self, event):
        if event["type"] == "PairCreated":
            token_info = await self.get_token_info(event["token0"])
            self.event_queue.add_event(("new_token", token_info))
        elif event["type"] in ["addLiquidityETH", "removeLiquidityETH"]:
            self.event_queue.add_event((event["type"], event))

    async def get_token_info(self, token_address):
        # Simulate getting token info
        return {
            "name": f"Token_{token_address[:6]}",
            "total_supply": random.randint(1000000, 1000000000),
            "decimals": 18,
            "symbol": f"TKN{token_address[:4]}",
            "deployer_addy": to_checksum_address(
                "0x" + "".join(random.choices("0123456789abcdef", k=40))
            ),
            "deployer_txHash": "0x" + "".join(random.choices("0123456789abcdef", k=64)),
            "basescan_deployer_url": f"https://basescan.org/address/{token_address}",
            "basescan_token_url": f"https://basescan.org/token/{token_address}",
            "dexscreener_url": f"https://dexscreener.com/base/{token_address}",
        }
