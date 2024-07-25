"""
TODO: look up token
TODO: save data after i filter to a sqlite database

"""

import json
import time

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
# DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

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

print(uniswap_addys["router"])

uniswap_router_contract = w3.eth.contract(
    address=uniswap_addys["router"], abi=universal_router_abi
)

uniswap_factory_contract = w3.eth.contract(
    address=uniswap_addys["UniswapV3Factory"], abi=uniswap_factory_abi
)

weth9_addy = uniswap_router_contract.functions.WETH9().call()
print(uniswap_router_contract.functions.factory().call())


def get_ERC20_token(event):
    # print(f"New Pool created: {event}")
    token0 = event["args"]["token0"]
    token1 = event["args"]["token1"]
    token0IsWeth = False
    token1IsWeth = False
    ERC20_ADDY = ""
    ERC20_LINK = ""

    print(f"Token0: {token0}")
    print(f"Token1: {token1}")
    print(f"Fee: {event['args']['fee']}")
    print(f"Pool Address: {event['args']['pool']}")
    print("----------------------------")

    if token0 == weth9_addy:
        token0IsWeth = True
    if token0 == weth9_addy:
        token1IsWeth = True

    if token0IsWeth:
        ERC20 = token0
        ERC20_ADDY = f"https://basescan.org/address/{ERC20}"
    if token1IsWeth:
        ERC20 = token1
        ERC20_ADDY = f"https://basescan.org/address/{ERC20}"

    print(f"This is the new token > {ERC20}")
    print(ERC20_ADDY)

    return (ERC20_ADDY, ERC20_LINK)


def check_new_pools(from_block, to_block):
    events = uniswap_factory_contract.events.PoolCreated.get_logs(
        fromBlock=from_block, toBlock=to_block
    )
    for event in events:
        erc20 = get_ERC20_token(event)
        print(erc20)


latest_block = None

while True:
    try:
        new_latest_block = w3.eth.get_block("latest")
        check_new_pools(17558419, 17564520)  # TODO: this is for debugging purposes
        # if latest_block is None:
        #     latest_block = new_latest_block - 1

        # if new_latest_block > latest_block:
        #     print(f"Checking blocks {latest_block + 1} to {new_latest_block}")
        #     check_new_pools(latest_block + 1, new_latest_block)
        #     latest_block = new_latest_block

    except Exception as e:
        print(f"An error occurred: {e}")

    time.sleep(3)  # Wait for 10 seconds before checking for new blocks
