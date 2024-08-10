from web3 import Web3
from pathlib import Path
import json

# Load contract information
with open('contract_info.json', 'r') as file:
    contract_info = json.load(file)

# RPC URLs
avax_rpc_url = "https://api.avax-test.network/ext/bc/C/rpc"  # Avalanche C-chain testnet
bsc_rpc_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet

# Connect to the networks
avax_web3 = Web3(Web3.HTTPProvider(avax_rpc_url))
bsc_web3 = Web3(Web3.HTTPProvider(bsc_rpc_url))

# Deployer details
deployer_address = "0xd7b33084078F1269e21734bA4E73b7f085414194"
private_key = "d4beb38bd527d38cb8f742a4bb7ab94eb8bcdd7d702f3c7f03a134d2781038e1"

# Load Source contract
source_contract = avax_web3.eth.contract(
    address=Web3.to_checksum_address(contract_info['source']['address']),
    abi=contract_info['source']['abi']
)

# Load Destination contract
destination_contract = bsc_web3.eth.contract(
    address=Web3.to_checksum_address(contract_info['destination']['address']),
    abi=contract_info['destination']['abi']
)

# Token addresses from the CSV
tokens = [
    "0xc677c31AD31F73A5290f5ef067F8CEF8d301e45c",
    "0x0773b81e0524447784CcE1F3808fed6AaA156eC8"
]

# Register tokens on the Source contract
for token in tokens:
    nonce = avax_web3.eth.get_transaction_count(deployer_address, 'pending')
    transaction = source_contract.functions.registerToken(
        Web3.to_checksum_address(token)
    ).build_transaction({
        'from': deployer_address,
        'nonce': nonce,
        'gas': 500000,
        'gasPrice': avax_web3.to_wei('50', 'gwei')
    })

    signed_txn = avax_web3.eth.account.sign_transaction(transaction, private_key=private_key)
    tx_hash = avax_web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"registerToken Transaction hash: {tx_hash.hex()}")

    avax_web3.eth.wait_for_transaction_receipt(tx_hash)

# Create tokens on the Destination contract
for token in tokens:
    nonce = bsc_web3.eth.get_transaction_count(deployer_address, 'pending')
    transaction = destination_contract.functions.createToken(
        Web3.to_checksum_address(token),
        "Wrapped Token",  # You can customize the token name
        "WTKN"  # You can customize the token symbol
    ).build_transaction({
        'from': deployer_address,
        'nonce': nonce,
        'gas': 1400000,
        'gasPrice': bsc_web3.to_wei('50', 'gwei')
    })

    signed_txn = bsc_web3.eth.account.sign_transaction(transaction, private_key=private_key)
    tx_hash = bsc_web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"createToken Transaction hash: {tx_hash.hex()}")

    bsc_web3.eth.wait_for_transaction_receipt(tx_hash)
