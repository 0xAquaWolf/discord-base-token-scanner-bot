import json
from web3 import Web3
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()
BASESCAN_API_TOKEN = os.getenv("BASESCAN_API_TOKEN")

# Connect to Base chain
rpc_url = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(rpc_url))

# Load contract ABIs and addresses
with open("uniswap_base_addys.json") as f:
    uniswap_addys = json.load(f)

with open("uniswap_router_abi.json") as f:
    universal_router_abi = json.load(f)

with open("uniswap_factory_abi.json") as f:
    uniswap_factory_abi = json.load(f)

with open("ERC20_ABI.json") as f:
    ERC20_ABI = json.load(f)

# Initialize contracts
uniswap_router_contract = w3.eth.contract(
    address=uniswap_addys["router"], abi=universal_router_abi
)

uniswap_factory_contract = w3.eth.contract(
    address=uniswap_addys["UniswapV3Factory"], abi=uniswap_factory_abi
)

weth9_addy = uniswap_router_contract.functions.WETH9().call()


def basescan_link(addy):
    return f"https://basescan.org/address/{addy}"


def get_ERC20_token(event):
    token0 = event["args"]["token0"]
    token1 = event["args"]["token1"]
    token0IsWeth = token0 == weth9_addy
    token1IsWeth = token1 == weth9_addy

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
    "ERC20_ABI",
    "get_ERC20_token",
    "basescan_link",
    "get_token_info",
    "get_deployer_info",
    "format_token_info",
]
