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
