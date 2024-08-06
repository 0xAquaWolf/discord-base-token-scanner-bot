import json
from web3 import Web3
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()
BASESCAN_API_TOKEN = os.getenv("BASESCAN_API_TOKEN")
# Get the absolute path of the current file
# current_file = os.path.abspath(__file__)

# # Get the directory containing the current file
# current_dir = os.path.dirname(current_file)

# # Get the parent directory (which should be 'src')
# src_dir = os.path.dirname(current_dir)

# # Get the project root directory (parent of 'src')
# BASE_PATH = os.path.dirname(src_dir)
# Connect to Base chain
rpc_url = "https://mainnet.base.org/"
# rpc_url = "https://base.llamarpc.com"
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Load contract ABIs and addresses
with open("./contracts/addresses/uniswap_base_addys.json") as f:
    uniswap_addys = json.load(f)

with open("./contracts/abis/uniswap_router_abi.json") as f:
    uniswap_router_abi = json.load(f)

with open("./contracts/abis/uniswap_factory_abi.json") as f:
    uniswap_factory_abi = json.load(f)

with open("./contracts/abis/ERC20_ABI.json") as f:
    ERC20_ABI = json.load(f)

# Initialize contracts
uniswap_router_contract = w3.eth.contract(
    address=uniswap_addys["UniswapV2Router"], abi=uniswap_router_abi
)

uniswap_factory_contract = w3.eth.contract(
    address=uniswap_addys["UniswapV2Factory"], abi=uniswap_factory_abi
)

weth_addy = uniswap_router_contract.functions.WETH().call()


def basescan_link(addy):
    return f"https://basescan.org/address/{addy}"


def basescan_tx_link(hash):
    return f"https://basescan.org/tx/{hash}"


def dexscreener_link(addy):
    return f"https://dexscreener.com/base/{addy}"


def get_ERC20_token(event):
    token0 = event["args"]["token0"]
    token1 = event["args"]["token1"]
    token0IsWeth = token0 == weth_addy
    token1IsWeth = token1 == weth_addy

    if token0IsWeth:
        ERC20_ADDY = token1
    elif token1IsWeth:
        ERC20_ADDY = token0
    else:
        # Handle case where neither token is WETH
        return None, None

    BASESCAN_LINK = basescan_link(ERC20_ADDY)
    return (ERC20_ADDY, BASESCAN_LINK)


def get_token_info(ERC20_ADDY):
    ERC20_CONTRACT = w3.eth.contract(address=ERC20_ADDY, abi=ERC20_ABI)

    try:
        name = ERC20_CONTRACT.functions.name().call()
        total_supply = ERC20_CONTRACT.functions.totalSupply().call()
        decimals = ERC20_CONTRACT.functions.decimals().call()
        symbol = ERC20_CONTRACT.functions.symbol().call()
    except Exception as e:
        print(f"Error getting token info for {ERC20_ADDY}: {e}")
        return None, None, None, None

    return name, total_supply, decimals, symbol


def get_deployer_info(ERC20_ADDY):
    url = f"https://api.basescan.org/api?module=contract&action=getcontractcreation&contractaddresses={ERC20_ADDY}&apikey={BASESCAN_API_TOKEN}"
    try:
        response = requests.get(url)
        data = response.json()

        if data["status"] == "1" and data["result"]:
            deployer_addy = data["result"][0]["contractCreator"]
            deployer_txHash = data["result"][0]["txHash"]
            return deployer_addy, deployer_txHash
        else:
            print(f"No deployer info found for {ERC20_ADDY}")
            return None, None
    except Exception as e:
        print(f"Error getting deployer info for {ERC20_ADDY}: {e}")
        return None, None


def format_token_info(token_info):
    """Format token information for display"""
    formatted_info = f"""
    Name: {token_info['name']}
    Symbol: {token_info['symbol']}
    Decimals: {token_info['decimals']}
    Total Supply: {token_info['total_supply']}
    Deployer Address: {token_info['deployer_addy']}
    Deployer Transaction: {token_info['deployer_txHash']}
    Basescan Token Link: {token_info['basescan_token_url']}
    Basescan Deployer Link: {token_info['basescan_deployer_url']}
    """
    return formatted_info


def print_token_info(token_info):
    print("New token detected:")
    print(f"Name: {token_info['name']}")
    print(f"Symbol: {token_info['symbol']}")
    print(f"Total Supply: {token_info['total_supply']}")
    print(f"Decimals: {token_info['decimals']}")
    print(f"Deployer Address: {token_info['deployer_addy']}")
    print(f"Deployer Transaction: {token_info['deployer_txHash']}")
    print(f"Basescan Deployer URL: {token_info['basescan_deployer_url']}")
    print(f"Basescan Token URL: {token_info['basescan_token_url']}")
    print("---")


# You might want to add more utility functions here as needed

# Test the connection
if w3.is_connected():
    print("Connected to Base chain network")
else:
    print("Failed to connect to the Base chain node")

    # Explicitly export the necessary components
__all__ = [
    "w3",
    "uniswap_factory_contract",
    "uniswap_router_contract",
    "ERC20_ABI",
    "get_ERC20_token",
    "basescan_link",
    "get_token_info",
    "get_deployer_info",
    "format_token_info",
    "dexscreener_link",
    "basescan_tx_link",
    "print_token_info",
    "weth_addy",
    "uniswap_addys",
]
