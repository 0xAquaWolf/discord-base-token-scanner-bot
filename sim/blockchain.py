import time
import random
from eth_utils import to_checksum_address


class SimulatedBlockchain:
    def __init__(self):
        self.current_block = 0
        self.events = ["PairCreated", "addLiquidityETH", "removeLiquidityETH"]

    def generate_event(self):
        self.current_block += 1
        event_type = random.choice(self.events)
        timestamp = int(time.time())

        if event_type == "PairCreated":
            return {
                "type": event_type,
                "block": self.current_block,
                "timestamp": timestamp,
                "token0": to_checksum_address(
                    "0x" + "".join(random.choices("0123456789abcdef", k=40))
                ),
                "token1": to_checksum_address(
                    "0x" + "".join(random.choices("0123456789abcdef", k=40))
                ),
                "pair": to_checksum_address(
                    "0x" + "".join(random.choices("0123456789abcdef", k=40))
                ),
            }
        else:
            return {
                "type": event_type,
                "block": self.current_block,
                "timestamp": timestamp,
                "token": to_checksum_address(
                    "0x" + "".join(random.choices("0123456789abcdef", k=40))
                ),
                "amount": random.randint(1, 1000000) / 1000,  # Simulated ETH amount
                "to": to_checksum_address(
                    "0x" + "".join(random.choices("0123456789abcdef", k=40))
                ),
                "deadline": timestamp + 3600,  # 1 hour from now
            }

    def get_latest_block(self):
        return self.current_block
