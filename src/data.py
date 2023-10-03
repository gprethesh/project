from ecdsa import SigningKey, SECP256k1
import asyncio
from datetime import datetime
import json
import time
from chain import create_new_block, create_and_add_transaction, create_db, add_block_to_chain
from main import BlockHeader, Block, Transaction
with open("config.json", "r") as f:
    config = json.load(f)

TRANSACTION_FEE = config["TRANSACTION_FEE"]
MINING_REWARD = config["MINING_REWARD"]
MAX_SUPPLY = config["MAX_SUPPLY"]
miner_address = config["minerAddress"]

def sign_transaction(transaction, private_key):
    sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
    hash_to_sign = transaction.calculate_hash()
    print(f"Hash in sign_transaction: {hash_to_sign}")
    signature = sk.sign(hash_to_sign.encode())
    transaction.signature = signature.hex()
    
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


async def test_blockchain():
    print("Starting blockchain test...")
    await create_db("hello")
    # Add your private keys here
    private_key_sender1 = "e265786c34e8dfa1a5801d51dfc3c26024b4651e35f5f834f5e00a8b25cce50d"
    private_key_sender2 = "f63795f1f00944217faa57bf6965eec798e1f7a3261c7542424ca7526d3f7af2"

    # Create a transaction and sign it
    transaction1 = Transaction(
      "ed0d2bd7e2aacb0dd0e0befe0f5d9b4df8381178ff03d506715a4bc0afe5adcd2a10c9cc39b065c6448430142312561c1a69a0104ef8f70fc063a6f1958e754d",
      "a8c2b097c5fbbfc2953090a56687b6aaa51b07946768deccacc5ba51890474afcdac4c602b09451ecc16a48f1ddf31bd89c8855d8010b8b11431d547d3a0bf79",
      90,
      TRANSACTION_FEE,
      'signature1',
      datetime.now().timestamp(),
       "id1"
    )
    
    sign_transaction(transaction1, private_key_sender2)
    
    
    # Create a transaction and sign it
    transaction2 = Transaction(
      "ed0d2bd7e2aacb0dd0e0befe0f5d9b4df8381178ff03d506715a4bc0afe5adcd2a10c9cc39b065c6448430142312561c1a69a0104ef8f70fc063a6f1958e754d",
      "6bdd4e125da26ff04bd119fed0626b7dc619e09ed099f6496775844436424e064e38e8d7dbc11a4568bc64366f01eaaab2f0de49f86839747413dabe2e259229",
      50,
      TRANSACTION_FEE,
      'signature1',
      datetime.now().timestamp(),
       "id1"
    )
    
    sign_transaction(transaction2, private_key_sender1)
   

    # Create a block and add the transaction
    block1 = await  create_new_block([transaction1], miner_address)

    blockx = await create_and_add_transaction(block1, [transaction1], miner_address)
    
    if blockx:
        await add_block_to_chain(blockx)

    
    # Create a block and add the transaction
    block2 = await  create_new_block([transaction2], miner_address)

    blockp = await create_and_add_transaction(block2, [transaction2], miner_address)
    
    if blockp:
        await add_block_to_chain(blockp)

# Run the tests


async def main():
    await test_blockchain()

# Run the tests
asyncio.run(main())

