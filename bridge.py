from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware #Necessary for POA chains
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
        api_url = f"https://api.avax-test.network/ext/bc/C/rpc" #AVAX C-chain testnet

    if chain == 'bsc':
        api_url = f"https://data-seed-prebsc-1-s1.binance.org:8545/" #BSC testnet

    if chain in ['avax','bsc']:
        w3 = Web3(Web3.HTTPProvider(api_url))
        # inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def getContractInfo(chain):
    """
        Load the contract_info file into a dictinary
        This function is used by the autograder and will likely be useful to you
    """
    p = Path(__file__).with_name(contract_info)
    try:
        with p.open('r')  as f:
            contracts = json.load(f)
    except Exception as e:
        print( "Failed to read contract info" )
        print( "Please contact your instructor" )
        print( e )
        sys.exit(1)

    return contracts[chain]

def scanBlocks(chain):
    """
        chain - (string) should be either "source" or "destination"
        Scan the last 5 blocks of the source and destination chains
        Look for 'Deposit' events on the source chain and 'Unwrap' events on the destination chain
        When Deposit events are found on the source chain, call the 'wrap' function the destination chain
        When Unwrap events are found on the destination chain, call the 'withdraw' function on the source chain
    """

    if chain not in ['source','destination']:
        print( f"Invalid chain: {chain}" )
        return
    
    #YOUR CODE HERE
    w3_src = connectTo(source_chain)
    w3_dst = connectTo(destination_chain)
    source_contracts = getContractInfo("source")
    destination_contracts = getContractInfo("destination")
    source_contract_address, src_abi = source_contracts["address"], source_contracts["abi"]
    destination_contract_address, dst_abi = destination_contracts["address"], destination_contracts["abi"]
    
    source_contract = w3_src.eth.contract(address=source_contract_address, abi=src_abi)
    destination_contract = w3_dst.eth.contract(address=destination_contract_address, abi=dst_abi)

    
    src_end_block = w3_src.eth.get_block_number()
    src_start_block = src_end_block - 5
    dst_end_block = w3_dst.eth.get_block_number()
    dst_start_block = dst_end_block - 5

    arg_filter = {}
    if chain == "source":  #Source
        
        event_filter = source_contract.events.Deposit.create_filter(fromBlock=src_start_block, toBlock = src_end_block, argument_filters=arg_filter)
        for event in event_filter.get_all_entries():
            txn = destination_contract.functions.wrap(event.args['token'], event.args['recipient'], event.args['amount']).build_transaction({
                'from': account_address,
                'chainId': w3_dst.eth.chain_id,
                'gas': 5000000,
                'nonce': w3_dst.eth.get_transaction_count(account_address)
            })
            signed_txn = w3_dst.eth.account.sign_transaction(txn, private_key=private_key)
            w3_dst.eth.send_raw_transaction(signed_txn.rawTransaction)

    elif chain == "destination":  #Destination
        
        event_filter = destination_contract.events.Unwrap.create_filter(fromBlock=dst_start_block, toBlock = dst_end_block, argument_filters=arg_filter)
        for event in event_filter.get_all_entries():
            txn = source_contract.functions.withdraw(event.args['underlying_token'], event.args['to'], event.args['amount']).build_transaction({
            'from': account_address,
            'chainId': w3_src.eth.chain_id,
            'gas': 1000000,
            'nonce': w3_src.eth.get_transaction_count(account_address)
            })
            signed_txn = w3_src.eth.account.sign_transaction(txn, private_key=private_key)
            w3_src.eth.send_raw_transaction(signed_txn.rawTransaction)
