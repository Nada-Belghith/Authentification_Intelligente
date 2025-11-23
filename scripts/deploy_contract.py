import json
import os
from pathlib import Path

from solcx import compile_standard, install_solc
from web3 import Web3

from backend.config import GANACHE_URL, CHAIN_ACCOUNT_ADDRESS, CHAIN_PRIVATE_KEY, CONTRACT_DATA_FILE


def compile_contract(sol_path: str):
    with open(sol_path, 'r', encoding='utf-8') as f:
        source = f.read()

    install_solc('0.8.17')
    compiled = compile_standard({
        'language': 'Solidity',
        'sources': {os.path.basename(sol_path): {'content': source}},
        'settings': {'outputSelection': {'*': {'*': ['abi', 'evm.bytecode']}}}
    }, solc_version='0.8.17')

    contract_name = list(compiled['contracts'][os.path.basename(sol_path)].keys())[0]
    contract_data = compiled['contracts'][os.path.basename(sol_path)][contract_name]
    abi = contract_data['abi']
    bytecode = contract_data['evm']['bytecode']['object']
    return abi, bytecode


def deploy(abi, bytecode):
    w3 = Web3(Web3.HTTPProvider(GANACHE_URL))
    if not w3.isConnected():
        raise RuntimeError(f"Cannot connect to Ganache at {GANACHE_URL}")

    account = w3.toChecksumAddress(CHAIN_ACCOUNT_ADDRESS)
    nonce = w3.eth.get_transaction_count(account)

    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    construct_txn = Contract.constructor().buildTransaction({
        'from': account,
        'nonce': nonce,
        'gas': 8000000,
        'gasPrice': w3.toWei('20', 'gwei')
    })

    signed = w3.eth.account.sign_transaction(construct_txn, private_key=CHAIN_PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    return receipt.contractAddress, abi


if __name__ == '__main__':
    sol_path = Path(__file__).resolve().parents[1] / 'contracts' / 'LogContract.sol'
    print(f"Compiling {sol_path}...")
    abi, bytecode = compile_contract(str(sol_path))
    print("Deploying contract to Ganache...")
    address, abi = deploy(abi, bytecode)
    print(f"Deployed at: {address}")

    # Write contract data so backend can use it
    data = {'address': address, 'abi': abi}
    Path(CONTRACT_DATA_FILE).write_text(json.dumps(data, indent=2))
    print(f"Wrote contract data to {CONTRACT_DATA_FILE}")
