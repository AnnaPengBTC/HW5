from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import sys
from pathlib import Path

source_chain = 'avax'
destination_chain = 'bsc'
contract_info = "contract_info.json"
private_key = "d4beb38bd527d38cb8f742a4bb7ab94eb8bcdd7d702f3c7f03a134d2781038e1"
account_address = '0xd7b33084078F1269e21734bA4E73b7f085414194'

def connectTo(chain):
    if chain == 'avax':
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc"
    elif chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/"
    else:
        raise ValueError(f"Unsupported chain: {chain}")

    w3 = Web3(Web3.HTTPProvider(api_url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    if not w3.isConnected():
        print(f"Failed to connect to {chain} chain")
        sys.exit(1)
        
    return w3

def getContractInfo(chain):
    p = Path(__file__).with_name(contract_info)
    try:
        with p.open('r') as f:
            contracts = json.load(f)
    except Exception as e:
        print("Failed to read contract info")
        print("Please contact your instructor")
        print(e)
        sys.exit(1)

    return contracts.get(chain, {})

def register_and_create_token(w3, contract_address, abi, token_address):
    contract = w3.eth.contract(address=contract_address, abi=abi)
    
    try:
        # Call registerToken
        register_txn = contract.functions.registerToken(token_address).build_transaction({
            'from': account_address,
            'chainId': w3.eth.chain_id,
            'gas': 1000000,  # Adjust gas as necessary
            'nonce': w3.eth.get_transaction_count(account_address)
        })
        signed_register_txn = w3.eth.account.sign_transaction(register_txn, private_key=private_key)
        register_tx_hash = w3.eth.send_raw_transaction(signed_register_txn.rawTransaction)
        print(f"registerToken transaction sent: {register_tx_hash.hex()}")
        w3.eth.wait_for_transaction_receipt(register_tx_hash)

        # Call createToken
        create_txn = contract.functions.createToken(token_address).build_transaction({
            'from': account_address,
            'chainId': w3.eth.chain_id,
            'gas': 1000000,  # Adjust gas as necessary
            'nonce': w3.eth.get_transaction_count(account_address)
        })
        signed_create_txn = w3.eth.account.sign_transaction(create_txn, private_key=private_key)
        create_tx_hash = w3.eth.send_raw_transaction(signed_create_txn.rawTransaction)
        print(f"createToken transaction sent: {create_tx_hash.hex()}")
        w3.eth.wait_for_transaction_receipt(create_tx_hash)

    except Exception as e:
        print(f"Error during registerToken/createToken: {e}")

def scanBlocks(chain):
    if chain not in ['source', 'destination']:
        print(f"Invalid chain: {chain}")
        return
    
    w3_src = connectTo(source_chain)
    w3_dst = connectTo(destination_chain)
    source_contracts = getContractInfo("source")
    destination_contracts = getContractInfo("destination")
    
    if not source_contracts or not destination_contracts:
        print(f"Contract information missing for {chain}")
        return
    
    source_contract_address, src_abi = source_contracts["address"], source_contracts["abi"]
    destination_contract_address, dst_abi = destination_contracts["address"], destination_contracts["abi"]
    token_address = "0xc677c31AD31F73A5290f5ef067F8CEF8d301e45c"  # Example token address
    
    # Register and create token on both chains
    register_and_create_token(w3_src, source_contract_address, src_abi, token_address)
    register_and_create_token(w3_dst, destination_contract_address, dst_abi, token_address)

    source_contract = w3_src.eth.contract(address=source_contract_address, abi=src_abi)
    destination_contract = w3_dst.eth.contract(address=destination_contract_address, abi=dst_abi)

    src_end_block = w3_src.eth.get_block_number()
    src_start_block = src_end_block - 5
    dst_end_block = w3_dst.eth.get_block_number()
    dst_start_block = dst_end_block - 5

    arg_filter = {}

    if chain == "source":
        event_filter = source_contract.events.Deposit.create_filter(fromBlock=src_start_block, toBlock=src_end_block, argument_filters=arg_filter)
        for event in event_filter.get_all_entries():
            print(f"Found Deposit event: {event}")
            try:
                txn = destination_contract.functions.wrap(event.args['token'], event.args['recipient'], event.args['amount']).build_transaction({
                    'from': account_address,
                    'chainId': w3_dst.eth.chain_id,
                    'gas': 1000000,  # Consider starting with a higher gas limit
                    'nonce': w3_dst.eth.get_transaction_count(account_address)
                })
                signed_txn = w3_dst.eth.account.sign_transaction(txn, private_key=private_key)
                tx_hash = w3_dst.eth.send_raw_transaction(signed_txn.rawTransaction)
                print(f"Wrap transaction sent: {tx_hash.hex()}")
            except Exception as e:
                print(f"Failed to send wrap transaction: {e}")

    elif chain == "destination":
        event_filter = destination_contract.events.Unwrap.create_filter(fromBlock=dst_start_block, toBlock=dst_end_block, argument_filters=arg_filter)
        for event in event_filter.get_all_entries():
            print(f"Found Unwrap event: {event}")
            try:
                txn = source_contract.functions.withdraw(event.args['underlying_token'], event.args['to'], event.args['amount']).build_transaction({
                    'from': account_address,
                    'chainId': w3_src.eth.chain_id,
                    'gas': 1000000,  # Consider starting with a higher gas limit
                    'nonce': w3_src.eth.get_transaction_count(account_address)
                })
                signed_txn = w3_src.eth.account.sign_transaction(txn, private_key=private_key)
                tx_hash = w3_src.eth.send_raw_transaction(signed_txn.rawTransaction)
                print(f"Withdraw transaction sent: {tx_hash.hex()}")
            except Exception as e:
                print(f"Failed to send withdraw transaction: {e}")
