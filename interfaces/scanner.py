import asyncio
from eth_abi import decode
from eth_utils import to_checksum_address
from utils.logger import setup_logger
from db.database import Database
from utils.token_utils import (
    w3,
    uniswap_factory_contract,
    get_ERC20_token,
    get_token_info,
    get_deployer_info,
    ERC20_ABI,
    uniswap_addys,
)

logger = setup_logger(__name__)


class BlockchainScanner:
    def __init__(self, blockchain, database: Database, event_queue, config):
        self.blockchain = blockchain
        self.event_queue = event_queue
        self.database = database
        self.config = config
        self.last_checked_block = None

    async def start_monitoring(self):
        while True:
            try:
                await self.monitor_new_pools()
                await self.monitor_liquidity_events()
                await asyncio.sleep(10)  # Adjust as needed
            except Exception as e:
                logger.error(f"Error in blockchain scanning: {e}")

    async def monitor_new_pools(self):
        try:
            new_latest_block = await self.blockchain.get_latest_block()
            new_latest_block = new_latest_block["number"]
            if self.last_checked_block is None:
                self.last_checked_block = new_latest_block - 1
            if new_latest_block > self.last_checked_block:
                events = await self.check_new_pools(
                    self.last_checked_block + 1, new_latest_block + 1
                )
                for event in events:
                    self.event_queue.add_event(("new_token", event["token_info"]))
                self.last_checked_block = new_latest_block
        except Exception as e:
            logger.error(f"Error in monitor_new_pools: {e}")

    async def check_new_pools(self, from_block, to_block):
        try:
            events = uniswap_factory_contract.events.PairCreated.get_logs(
                fromBlock=from_block, toBlock=to_block
            )
            processed_events = []
            for event in events:
                try:
                    ERC20_ADDY, BASESCAN_LINK = get_ERC20_token(event)
                    if ERC20_ADDY:
                        token_info = await self.get_token_info(
                            ERC20_ADDY, BASESCAN_LINK
                        )
                        # processed_events.append({"token_info": token_info})
                        await self.database.insert_new_token(token_info)
                        logger.info(f"Processed new token: {token_info['name']}")
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
            return processed_events
        except Exception as e:
            logger.error(f"Error in check_new_pools: {e}")
            return []

    async def get_token_info(self, ERC20_ADDY, BASESCAN_LINK):
        name, total_supply, decimals, symbol = get_token_info(ERC20_ADDY)
        deployer_addy, deployer_txHash = get_deployer_info(ERC20_ADDY)
        token_info = {
            "name": name,
            "total_supply": total_supply,
            "decimals": decimals,
            "symbol": symbol,
            "deployer_addy": deployer_addy,
            "deployer_txHash": f"https://basescan.org/tx/{deployer_txHash}",
            "basescan_deployer_url": f"https://basescan.org/address/{deployer_addy}",
            "basescan_token_url": BASESCAN_LINK,
            "dexscreener_url": f"https://dexscreener.com/base/{ERC20_ADDY}",
        }
        return token_info

    async def monitor_liquidity_events(self):
        add_liquidity_eth_selector = w3.keccak(
            text="addLiquidityETH(address,uint256,uint256,uint256,address,uint256)"
        ).hex()[:10]
        add_liquidity_eth_selector_bytes = bytes.fromhex(add_liquidity_eth_selector[2:])

        remove_liquidity_eth_selector = w3.keccak(
            text="removeLiquidityETH(address,uint256,uint256,uint256,address,uint256)"
        ).hex()[:10]
        remove_liquidity_eth_selector_bytes = bytes.fromhex(
            remove_liquidity_eth_selector[2:]
        )

        try:
            new_latest_block = await self.blockchain.get_latest_block()
            new_latest_block_number = new_latest_block["number"]

            if self.last_checked_block is None:
                self.last_checked_block = new_latest_block_number - 100

            if new_latest_block_number > self.last_checked_block:
                for block_number in range(
                    self.last_checked_block + 1, new_latest_block_number + 1
                ):
                    block = await self.blockchain.get_block(block_number)
                    for tx in block.transactions:
                        if tx["to"] == uniswap_addys["UniswapV2Router"]:
                            input_data = tx["input"]
                            if input_data.startswith(add_liquidity_eth_selector_bytes):
                                await self.process_add_liquidity_eth_event(tx)
                            elif input_data.startswith(
                                remove_liquidity_eth_selector_bytes
                            ):
                                await self.process_remove_liquidity_eth_event(tx)

                self.last_checked_block = new_latest_block_number

        except Exception as e:
            logger.error(f"Error in monitor_liquidity_events: {e}")

    async def process_remove_liquidity_eth_event(self, tx):
        try:
            tx_hash = tx["hash"].hex()
            input_data = tx["input"]
            data = input_data.hex()[10:]
            param_types = [
                "address",
                "uint256",
                "uint256",
                "uint256",
                "address",
                "uint256",
            ]
            decoded = decode(param_types, bytes.fromhex(data))

            token_address = to_checksum_address(decoded[0])
            liquidity = decoded[1]
            amount_token_min = decoded[2]
            amount_eth_min = decoded[3]
            to_address = to_checksum_address(decoded[4])
            deadline = decoded[5]

            token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
            token_name = token_contract.functions.name().call()
            token_symbol = token_contract.functions.symbol().call()
            token_decimals = token_contract.functions.decimals().call()

            event_data = {
                "event_type": "removeLiquidityETH",
                "token_name": token_name,
                "token_symbol": token_symbol,
                "token_decimals": token_decimals,
                "liquidity": w3.from_wei(liquidity, "ether"),
                "token_min": w3.from_wei(amount_token_min, "ether"),
                "eth_min": w3.from_wei(amount_eth_min, "ether"),
                "to_address": to_address,
                "deadline": deadline,
                "tx_hash": tx_hash,
            }

            # self.event_queue.add_event(("removeLiquidityETH", event_data))
            await self.database.insert_liquidity_event("removeLiquidityETH", event_data)
            logger.info(f"Processed removeLiquidityETH event: {event_data}")

        except Exception as e:
            logger.error(
                f"Error processing removeLiquidityETH event: {e}", exc_info=True
            )

    async def process_add_liquidity_eth_event(self, tx):
        try:
            tx_hash = tx["hash"].hex()
            input_data = tx["input"]
            data = input_data.hex()[10:]
            param_types = [
                "address",
                "uint256",
                "uint256",
                "uint256",
                "address",
                "uint256",
            ]
            decoded = decode(param_types, bytes.fromhex(data))

            token_address = to_checksum_address(decoded[0])
            amount_token_desired = decoded[1]
            amount_token_min = decoded[2]
            amount_eth_min = decoded[3]
            to_address = to_checksum_address(decoded[4])
            deadline = decoded[5]

            eth_amount = tx["value"]

            token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
            token_name = token_contract.functions.name().call()
            token_symbol = token_contract.functions.symbol().call()
            token_decimals = token_contract.functions.decimals().call()

            event_data = {
                "event_type": "addLiquidityETH",
                "token_name": token_name,
                "token_symbol": token_symbol,
                "token_decimals": token_decimals,
                "eth_amount": w3.from_wei(eth_amount, "ether"),
                "token_amount": w3.from_wei(amount_token_desired, "ether"),
                "token_min": w3.from_wei(amount_token_min, "ether"),
                "eth_min": w3.from_wei(amount_eth_min, "ether"),
                "to_address": to_address,
                "deadline": deadline,
                "tx_hash": tx_hash,
            }

            # self.event_queue.add_event(("addLiquidityETH", event_data))
            await self.database.insert_liquidity_event("addLiquidityETH", event_data)
            logger.info(f"Processed addLiquidityETH event: {event_data}")

        except Exception as e:
            logger.error(f"Error processing addLiquidityETH event: {e}", exc_info=True)
