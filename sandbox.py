import json

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()
# DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

uniswap_base_json = open("uniswap-base.json")
uniswap_addys = json.load(uniswap_base_json)
print(uniswap_addys)

universal_router_json = open("universal_router.json")
universal_router_abi = json.load(universal_router_json)

# TODO: save data after i filter to a sqlite database
# TODO: add formating keybinding w

rpc_url = "https://mainnet.base.org"
w3 = Web3(Web3.HTTPProvider(rpc_url))

if w3.is_connected():
    print("Connected to Base chain network")
else:
    print("Failed to connect to the Base chain node")

# Contract address
contract_address = "0x2626664c2603336E57B271c5C0b26F421741e481"

# Contract ABI (you need to replace this with the actual ABI of your contract)
contract_abi = universal_router_abi
print(contract_abi)

uniswap_router_contract = w3.eth.contract(address=contract_address, abi=contract_abi)
print(uniswap_router_contract)
print("WETH9 ADDY")
print(uniswap_router_contract.functions.WETH9().call())
print("FACTORY ADDY")
print(uniswap_router_contract.functions.factory().call())
