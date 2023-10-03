import unittest
from main import BlockHeader, Block, Transaction
from chain import calculate_hash_for_transaction, get_balance, update_balance
from merkletree import MerkleTree
import json
import ecdsa
from ecdsa import SigningKey, VerifyingKey, SECP256k1
ec = SigningKey.generate(curve=SECP256k1)

with open("config.json", "r") as f:
    config = json.load(f)

TRANSACTION_FEE = config["TRANSACTION_FEE"]
MINING_REWARD = config["MINING_REWARD"]
MAX_SUPPLY = config["MAX_SUPPLY"]

async def validate_transfer(transaction):
    if transaction["sender"] == "genesis":
        print("Genesis Block detected")
        await update_balance(transaction["receiver"], transaction["amount"])
        return True
    
    print("i'm in validate transfer")
    print("transactionSender", transaction["sender"])
    key = ec.key_from_public_key(transaction["sender"].encode("utf-8"), curve=ecdsa.SECP256k1)
    print("key", key)
    valid_signature = key.verify(calculate_hash_for_transaction(transaction).encode("utf-8"), bytes.fromhex(transaction["signature"]))

    if not valid_signature:
        print(f"Invalid transaction from {transaction['sender']} due to invalid signature")
        return False

    try:
        sender_balance = await get_balance(transaction["sender"])
        sender_balance = sender_balance or 0
        if transaction["amount"] + TRANSACTION_FEE > sender_balance:
            print(f"Invalid transaction from {transaction['sender']} due to insufficient funds")
            return False
        else:
            return True
    except Exception as e:
        print("Error fetching balance:", e)
        return False

class TestMerkleTree(unittest.TestCase):
    def test_merkle_tree(self):
        # Define a list of transactions
        transactions = [
            Transaction('sender1', 'receiver1', 10, 0.1, 'signature1', 1622641074000, 'id1'),
            Transaction('sender2', 'receiver2', 20, 0.2, 'signature2', 1622641075000, 'id2'),
            Transaction('sender3', 'receiver3', 30, 0.3, 'signature3', 1622641076000, 'id3')
        ]

        # Create a Merkle tree from the transactions
        merkle_tree = MerkleTree(transactions)

       # Print the Merkle root
        print("Merkle root:", merkle_tree.get_merkle_root())
        
class TestValidateTransfer(unittest.IsolatedAsyncioTestCase):
    async def test_validate_transfer(self):
        # Define a transaction
        transaction = {
            "sender": "genesis",
            "receiver": "receiver1",
            "amount": 10,
            "signature": "signature1"
        }

        # Call the validate_transfer function
        result = await validate_transfer(transaction)

        # Check if the result is True
        self.assertTrue(result)

        # Define a transaction with invalid signature
        transaction = {
            "sender": "sender1",
            "receiver": "receiver1",
            "amount": 10,
            "signature": "invalid_signature"
        }

        # Call the validate_transfer function
        result = await validate_transfer(transaction)

        # Check if the result is False
        self.assertFalse(result)



if __name__ == '__main__':
    unittest.main()
