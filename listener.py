from web3 import Web3
from web3.contract import Contract
from web3.providers.rpc import HTTPProvider
from web3.middleware import geth_poa_middleware # Necessary for POA chains
import json
from datetime import datetime
import pandas as pd
import csv
import os

eventfile = 'deposit_logs.csv'

def scanBlocks(chain, start_block, end_block, contract_address):
    """
    chain - string (Either 'bsc' or 'avax')
    start_block - integer first block to scan
    end_block - integer last block to scan
    contract_address - the address of the deployed contract

    This function reads "Deposit" events from the specified contract, 
    and writes information about the events to the file "deposit_logs.csv"
    """
    if chain == 'avax':
        api_url = "https://api.avax-test.network/ext/bc/C/rpc"  # AVAX C-chain testnet
    elif chain == 'bsc':
        api_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC testnet
    else:
        print("Unsupported chain.")
        return

    w3 = Web3(Web3.HTTPProvider(api_url))

    if chain in ['avax', 'bsc']:
        # Inject the poa compatibility middleware to the innermost layer
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)

    DEPOSIT_ABI = json.loads('[ { "anonymous": false, "inputs": [ { "indexed": true, "internalType": "address", "name": "token", "type": "address" }, { "indexed": true, "internalType": "address", "name": "recipient", "type": "address" }, { "indexed": false, "internalType": "uint256", "name": "amount", "type": "uint256" } ], "name": "Deposit", "type": "event" }]')
    contract = w3.eth.contract(address=contract_address, abi=DEPOSIT_ABI)

    arg_filter = {}

    if start_block == "latest":
        start_block = w3.eth.get_block_number()
    if end_block == "latest":
        end_block = w3.eth.get_block_number()

    if end_block < start_block:
        print(f"Error: end_block < start_block!")
        print(f"end_block = {end_block}")
        print(f"start_block = {start_block}")
        return

    if start_block == end_block:
        print(f"Scanning block {start_block} on {chain}")
    else:
        print(f"Scanning blocks {start_block} - {end_block} on {chain}")

    if end_block - start_block < 30:
        event_filter = contract.events.Deposit.create_filter(fromBlock=start_block, toBlock=end_block, argument_filters=arg_filter)
        events = event_filter.get_all_entries()
        write_events_to_csv(events, chain)
    else:
        for block_num in range(start_block, end_block + 1):
            event_filter = contract.events.Deposit.create_filter(fromBlock=block_num, toBlock=block_num, argument_filters=arg_filter)
            events = event_filter.get_all_entries()
            write_events_to_csv(events, chain)

def write_events_to_csv(events, chain):
    print(events)
    with open(eventfile, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not (os.path.isfile(eventfile) and os.path.getsize(eventfile) > 0):
            writer.writerow(["chain", "token", "recipient", "amount", "transactionHash", "address"])
        for event in events:
            print("The event is", event)
            if event:
                writer.writerow([
                    chain,
                    event["args"]["token"],
                    event["args"]["recipient"],
                    str(event["args"]["amount"]),
                    event["transactionHash"].hex(),
                    event["address"]
                ])
