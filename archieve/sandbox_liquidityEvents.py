"""
TODO: Re-Architech the bot so that it run asyncio with co-routines for every process
TODO: Impliment a process manger that oversees all of the coroutines
TODO: Create a event queue
TODO: Message handler
TODO: Impliment a way to handle error messages and logs
TODO: Figure out how i'm going to configure it so that i can build the core engine and
then swap out any settings without having to rewrite the code

TODO: record how much liquidity is added
- How much ETH
- How much of the created token
- How much LP the deployer recieved

TODO: update discord bot with addLiquidityETH

TODO: save to sqlite db

TODO: monitor for the remove liquidity event as well
- create a seperate channel
- create

- Handle this off of stream
TODO: create another bot
TODO: create a sandbox channel for testing all types of discord features


TODO: removedLiqidityETH Event
"""

import json
import time
from dotenv import load_dotenv
from web3 import Web3
from token_utils import basescan_tx_link

load_dotenv()

rpc_url = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(rpc_url))

if w3.is_connected():
    print("Connected to Base chain network")
else:
    print("Failed to connect to the Base chain node")

with open("uniswap_base_addys.json") as f:
    uniswap_addys = json.load(f)
with open("uniswap_router_abi.json") as f:
    universal_router_abi = json.load(f)
with open("uniswap_factory_abi.json") as f:
    uniswap_factory_abi = json.load(f)
with open("ERC20_ABI.json") as f:
    ERC20_ABI = json.load(f)

print(uniswap_addys["UniswapV2Router"])

uniswap_router_contract = w3.eth.contract(
    address=uniswap_addys["UniswapV2Router"], abi=universal_router_abi
)
uniswap_factory_contract = w3.eth.contract(
    address=uniswap_addys["UniswapV2Factory"], abi=uniswap_factory_abi
)


def handle_event(block_number):
    block = w3.eth.get_block(block_number, full_transactions=True)
    add_liquidity_eth_selector = w3.keccak(
        text="addLiquidityETH(address,uint256,uint256,uint256,address,uint256)"
    ).hex()[:10]
    add_liquidity_eth_selector_bytes = bytes.fromhex(
        add_liquidity_eth_selector[2:]
    )  # Remove '0x' and convert to bytes
    for tx in block.transactions:
        if tx["to"] == uniswap_addys["UniswapV2Router"]:
            input_data = tx["input"]
            if input_data.startswith(add_liquidity_eth_selector_bytes):
                print(
                    f"addLiquidityETH transaction found: {basescan_tx_link(tx['hash'].hex())}"
                )


def main():
    latest_block = w3.eth.get_block("latest")["number"]
    while True:
        try:
            current_block = w3.eth.get_block("latest")["number"]
            if current_block > latest_block:
                for block_number in range(latest_block + 1, current_block + 1):
                    handle_event(block_number)
                latest_block = current_block
        except Exception as e:
            print(f"An error occurred: {e}")
        time.sleep(2)


if __name__ == "__main__":
    main()
