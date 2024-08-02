from eth_abi import decode
from eth_utils import to_checksum_address

# The input data
input_data = "0xf305d719000000000000000000000000e966f7aff2d40fdc0fdb8d9dba3f5cac8fef42e400000000000000000000000000000000000000000000020776437bb35e80000000000000000000000000000000000000000000000000000000000000000003e800000000000000000000000000000000000000000000000000000000000003e800000000000000000000000091a2599d96df07f8770f77f4903f74b385b66d990000000000000000000000000000000000000000000000000000000066abc43f"

# Remove '0x' prefix and the function selector (first 4 bytes)
data = input_data[10:]

# Define the types of the function parameters
param_types = ["address", "uint256", "uint256", "uint256", "address", "uint256"]

# Decode the input data
decoded = decode(param_types, bytes.fromhex(data))

# Function signature
function_signature = "addLiquidityETH(address token, uint256 amountTokenDesired, uint256 amountTokenMin, uint256 amountETHMin, address to, uint256 deadline)"

# Print the results
print(f"Function: {function_signature}")
print(f"MethodID: {input_data[:10]}")
for i, (param, value) in enumerate(zip(param_types, decoded)):
    if param == "address":
        value = to_checksum_address(value)
    print(f"[{i}]: {value}")
