import os
import time
from web3 import Web3
from web3.middleware import geth_poa_middleware
from web3.exceptions import TransactionNotFound
from hexbytes import HexBytes


class BlockchainService:
    def __init__(self, polygon_rpc_url: str, contract_address: str):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv('POLYGON_RPC_URL')))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.contract_address = self.w3.toChecksumAddress(
            os.getenv('CONTRACT_ADDRESS'))

        self.contract_abi = [

            {
                "inputs": [
                    {
                        "internalType": "string",
                                        "name": "description",
                                                "type": "string"
                    },
                    {
                        "internalType": "uint256",
                                        "name": "deadline",
                                                "type": "uint256"
                    },
                    {
                        "internalType": "string[]",
                                        "name": "optionDescriptions",
                                                "type": "string[]"
                    }
                ],
                "name": "addProposal",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [],
                "name": "getProposalCount",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "uint256",
                                        "name": "",
                                                "type": "uint256"
                    }
                ],
                "name": "proposals",
                "outputs": [
                    {
                        "internalType": "string",
                        "name": "description",
                        "type": "string"
                    },
                    {
                        "internalType": "uint256",
                        "name": "deadline",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                                        "name": "_voter",
                                                "type": "address"
                    },
                    {
                        "internalType": "bytes32",
                                        "name": "_hashedID",
                                                "type": "bytes32"
                    },
                    {
                        "internalType": "string",
                                        "name": "_ipfsHash",
                                                "type": "string"
                    }
                ],
                "name": "register",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "uint256",
                                        "name": "proposalIndex",
                                                "type": "uint256"
                    }
                ],
                "name": "tallyVotes",
                "outputs": [
                    {
                        "internalType": "uint256",
                        "name": "winningOption_",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "uint256",
                                        "name": "proposalIndex",
                                                "type": "uint256"
                    },
                    {
                        "internalType": "uint256",
                                        "name": "optionIndex",
                                                "type": "uint256"
                    }
                ],
                "name": "vote",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "address",
                                        "name": "",
                                                "type": "address"
                    }
                ],
                "name": "voters",
                "outputs": [
                    {
                        "internalType": "bytes32",
                        "name": "hashedID",
                        "type": "bytes32"
                    },
                    {
                        "internalType": "string",
                        "name": "ipfsHash",
                        "type": "string"
                    },
                    {
                        "internalType": "bool",
                        "name": "hasVoted",
                        "type": "bool"
                    },
                    {
                        "internalType": "uint256",
                        "name": "vote",
                        "type": "uint256"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]

        self.contract = self.w3.eth.contract(
            address=self.contract_address, abi=self.contract_abi)

    def hexbytes_to_string(self, dictionary):
        for key, value in dictionary.items():
            if isinstance(value, HexBytes):
                dictionary[key] = value.hex()
        return dictionary

    def attribute_dict_to_dict(self, attr_dict):
        if isinstance(attr_dict, dict):
            for key in attr_dict:
                attr_dict[key] = self.attribute_dict_to_dict(attr_dict[key])
            return dict(attr_dict)
        elif isinstance(attr_dict, (list, tuple)):
            return [self.attribute_dict_to_dict(elem) for elem in attr_dict]
        else:
            return attr_dict

    def register(self, hashed_id: str, username: str):
        account_private_key = os.getenv('ACCOUNT_PRIVATE_KEY')
        account_address = self.w3.eth.account.privateKeyToAccount(
            account_private_key).address

        # Convert the hashed_id to bytes32
        hashed_id_bytes32 = Web3.toBytes(text=hashed_id)

        nonce = self.w3.eth.getTransactionCount(account_address)
        txn_dict = self.contract.functions.register(
            account_address,
            hashed_id_bytes32,
            username
        ).buildTransaction({
            'chainId': 80001,  # Polygon Mumbai
            'gas': 197000,
            'gasPrice': self.w3.toWei('8.939766966933332', 'gwei'),
            'nonce': nonce,
        })

        signed_txn = self.w3.eth.account.signTransaction(
            txn_dict, account_private_key)
        result = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)

        # Wait for the transaction receipt
        retry_count = 0
        txn_receipt = None
        while retry_count < 30:
            try:
                txn_receipt = self.w3.eth.waitForTransactionReceipt(result)
                break
            except TransactionNotFound:
                retry_count += 1
                time.sleep(1)

        if txn_receipt is None:
            return {'status': 'failed', 'error': 'timeout'}

        # Convert AttributeDict to dictionary
        txn_receipt_dict = self.attribute_dict_to_dict(dict(txn_receipt))
        txn_receipt_dict = self.hexbytes_to_string(txn_receipt_dict)

        return {'status': 'added', 'txn_receipt': txn_receipt_dict, 'username': username}

    def vote(self, proposal_index: int, option_index: int, hashed_id: str):
        account_private_key = os.getenv('ACCOUNT_PRIVATE_KEY')
        account_address = self.w3.eth.account.privateKeyToAccount(
            account_private_key).address

        nonce = self.w3.eth.getTransactionCount(account_address)
        txn_dict = self.contract.functions.vote(
            proposal_index,
            option_index
        ).buildTransaction({
            'chainId': 80001,  # Polygon Mumbai
            'gas': 197000,
            'gasPrice': self.w3.toWei('8.939766966933332', 'gwei'),
            'nonce': nonce,
        })

        signed_txn = self.w3.eth.account.signTransaction(
            txn_dict, account_private_key)
        result = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)

        # Wait for the transaction receipt
        retry_count = 0
        txn_receipt = None
        while retry_count < 30:
            try:
                txn_receipt = self.w3.eth.waitForTransactionReceipt(result)
                break
            except TransactionNotFound:
                retry_count += 1
                time.sleep(1)

        if txn_receipt is None:
            return {'status': 'failed', 'error': 'timeout'}

        # Convert AttributeDict to dictionary
        txn_receipt_dict = self.attribute_dict_to_dict(dict(txn_receipt))
        txn_receipt_dict = self.hexbytes_to_string(txn_receipt_dict)

        return {'status': 'success', 'txn_receipt': txn_receipt_dict}
