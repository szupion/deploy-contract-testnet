import json
import random
import string
from solcx import compile_standard, install_solc
from web3 import Web3
from datetime import datetime
import uuid
import time

# Install Solidity compiler version 0.8.0
install_solc('0.8.0')

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

min_delay = config['min_transaction_delay']
max_delay = config['max_transaction_delay']
retry_delay = config['retry_delay']

# Connect to RPC networks CELO, OP, BASE
rpc_urls = {
    "celo": "https://celo-alfajores.infura.io/",
    "op": "https://optimism-sepolia.infura.io/",
    "base": "https://base-sepolia.infura.io/"
}

# Load wallets
with open('wallets.json', 'r') as file:
    wallets_data = json.load(file)
    wallets = wallets_data['wallets']

# Generate a random contract name
def generate_random_name():
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    unique_name = f"Contract_{random_string}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    return unique_name

# Compile and deploy contract
def deploy_contract(private_key, rpc_url, network_name):
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = w3.eth.account.from_key(private_key)

    with open("SimpleStorage.sol", "r") as file:
        simple_storage_file = file.read()

    compiled_sol = compile_standard({
        "language": "Solidity",
        "sources": {"SimpleStorage.sol": {"content": simple_storage_file}},
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "metadata", "evm.bytecode"]
                }
            }
        }
    }, solc_version="0.8.0")

    bytecode = compiled_sol['contracts']['SimpleStorage.sol']['SimpleStorage']['evm']['bytecode']['object']
    abi = compiled_sol['contracts']['SimpleStorage.sol']['SimpleStorage']['abi']

    contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    # Get current nonce before sending a transaction
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    contract_name = generate_random_name()

    transaction = contract.constructor(contract_name).build_transaction({
        'chainId': w3.eth.chain_id,
        'gas': 2000000,
        'gasPrice': gas_price,
        'nonce': nonce,
    })

    signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
    try:
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        return tx_hash.hex(), contract_name
    except Exception as e:
        print(f"Error during contract deployment: {str(e)}")
        return None, None

# Deploy contracts for each wallet
failed_deployments = []

for wallet in wallets:
    private_key = wallet
    for network_name, network_url in rpc_urls.items():
        success = False
        for attempt in range(3):
            tx_hash, contract_name = deploy_contract(private_key, network_url, network_name)
            if tx_hash:
                print(f"Contract {contract_name} deployed from wallet {private_key} in network {network_name}: {tx_hash}")
                success = True
                time.sleep(random.randint(min_delay, max_delay))
                break
            else:
                print(f"Attempt {attempt + 1} failed for wallet {private_key} in network {network_name}")
                time.sleep(retry_delay)
        
        if not success:
            print(f"Failed to deploy contract from wallet {private_key} in network {network_name}")
            failed_deployments.append(private_key)

# Save failed private keys to file
if failed_deployments:
    with open('failed_deployments.json', 'w') as file:
        json.dump(failed_deployments, file)
    print("Failed deployments saved in 'failed_deployments.json'.")
