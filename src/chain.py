import os
import leveldb
import hashlib
import time
import json
from main import BlockHeader, Block, Transaction
from tp import remove_transactions, get_transaction_pool, add_to_transaction_pool
from merkletree import MerkleTree
import ecdsa
from ecdsa import SigningKey, VerifyingKey, SECP256k1, BadSignatureError
ec = SigningKey.generate(curve=SECP256k1)
import binascii
import copy
import asyncio
import itertools

lock = asyncio.Lock()


with open("config.json", "r") as f:
    config = json.load(f)

TRANSACTION_FEE = config["TRANSACTION_FEE"]
MINING_REWARD = config["MINING_REWARD"]
MAX_SUPPLY = config["MAX_SUPPLY"]

db = None
blockchain = [];
# tp = []

difficulty = 0x1
maximum_target = int("0x000FFFFFFFFF0000000000000000000000000000000000000000000000000000", 16)
target = maximum_target // difficulty

async def create_db(peer_id):
    global db
    dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", peer_id)
    
    if not os.access(dir_path, os.F_OK):
        # If the code reaches here, it means that the directory does not exist.
        os.makedirs(dir_path, exist_ok=True)
        print(f"Created directory {dir_path}")
        
        # Now, as the directory was not existing, create the genesis block.
        try:
            db = leveldb.LevelDB(dir_path)
            genesis_block = await create_genesis_block()
            blockchain.append(genesis_block)
            await store_block(genesis_block)
            print("Genesis Block Created.")
        except Exception as e:
            # Some other error occurred while creating genesis block.
            print("Error creating genesis block or opening database:", e)
    else:
        try:
            db = leveldb.LevelDB(dir_path)
        except Exception as e:
            # Some error occurred while opening the database.
            print("Error opening database:", e)



def calculate_hash_for_block(block):
    # Convert all block attributes to strings
    version = str(block['block_header']['version'])
    previous_block_header = str(block['block_header']['previousBlockHeader'])
    merkle_root = str(block['block_header']['merkleRoot'])
    timestamp = str(block['block_header']['time'])
    difficulty = str(block['block_header']['difficulty'])

    # Concatenate the block attributes
    block_string = version + previous_block_header + merkle_root + timestamp + difficulty

    # Convert the block string to bytes
    data = block_string.encode('utf-8')

    # Calculate the SHA-256 hash
    sha256_hash = hashlib.sha256(data)

    return sha256_hash.hexdigest()


async def create_genesis_block():
    print("Calling genesis block")
    timestamp = 1690365924213
    previous_block_header = "0000000000000000000000000000000000000000000000000000000000000000"
    version = "1.0.0"
    merkle_root = "bb77e380f6d0ae7a842dc47a11b4d6a46523b05295eb86d4a583e59b90c1cbb5"
    difficulty= "0x1"
    block_header = BlockHeader(version, previous_block_header, merkle_root, timestamp, difficulty)

    # Create a transaction
    sender = "genesis"
    receiver = "ed0d2bd7e2aacb0dd0e0befe0f5d9b4df8381178ff03d506715a4bc0afe5adcd2a10c9cc39b065c6448430142312561c1a69a0104ef8f70fc063a6f1958e754d"
    amount = 100000,
    fee = 0,
    signature = None,
    time = timestamp,
    id = "id1"
    transaction = Transaction(sender, receiver, amount, fee, signature, time, id)

    # Add the transaction to the block
    transactions = [transaction]

    index = 0
    block = Block(block_header, index, transactions, transactions)
    
    block.blockHeader.hash = calculate_hash_for_block(block.to_dict())

    await update_balance(receiver, amount)
    block_dict = block.to_dict()

    return block_dict


def serialize_transaction(tx_object):
    return vars(tx_object)

def calculate_hash_for_blockX(block_string):
    sha = hashlib.sha256()
    sha.update(block_string.encode())  # Encoding the string to bytes
    return sha.hexdigest()

def object_to_dict(obj):
    if hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return obj

def mine_hash(Realblock):
    global target, difficulty

    # If nonce not in block, initialize it
    if 'nonce' not in Realblock:
        Realblock['nonce'] = 0

    # Convert the custom objects to dictionaries
    Realblock = {key: object_to_dict(value) for key, value in Realblock.items()}
    
    

    # Convert transactions list elements to dictionaries
    if 'transactions' in Realblock:
        Realblock['transactions'] = [object_to_dict(tx) for tx in Realblock['transactions']]
    if 'tx' in Realblock:
        Realblock['tx'] = [object_to_dict(tx) for tx in Realblock['tx']]

    # Convert the dictionary to a string
    
    block_string = json.dumps(Realblock, sort_keys=True)

    # Calculate initial hash
    hash = calculate_hash_for_blockX(block_string)
    
    print("mining for hash", hash)
    # Mining logic
    while int(hash, 16) > target:
        Realblock['nonce'] += 1
        block_string = json.dumps(Realblock, sort_keys=True)
        hash = calculate_hash_for_blockX(block_string)
        
    Realblock['block_header']['hash'] = hash
    print("Hash found:", hash)
    
    return Realblock  


async def reward_miner(block):
    try:
        # Check that the first transaction is from 'coinbase'
        if block["transactions"][0]["sender"] != "coinbase":
            raise Exception("First transaction is not from 'coinbase'")

        miner_address = block["transactions"][0]["receiver"]

        # Fetch and wait for the miner's balance
        miner_balance = await get_balance(miner_address)
        miner_balance = miner_balance or 0

        total_transaction_fees = 0

        # Start i at 1 to skip the coinbase transaction
        for i in range(1, len(block["transactions"])):
            total_transaction_fees += block["transactions"][i]["fee"]

        # Update and wait for the miner's balance to be updated
        await update_balance(
            miner_address,
            miner_balance + total_transaction_fees + MINING_REWARD
        )
    except Exception as e:
        print(f"Failed to reward miner: {e}")

async def create_new_block(transactions, miner_address):
   
    user_transactions = transactions.copy() # Copy the original transactions first

    tx = [transaction for transaction in user_transactions if transaction.sender != "coinbase" and transaction.sender != "system"]

    block_header = await create_new_block_header(transactions)
    
    index = await get_block_height() + 1
    

    # Use block_transactions for the transactions of new_block
    # And use tx for the tx field of new_block
    new_block = {
        "block_header": block_header,
        "index": index,
        "transactions": transactions,
        "tx": tx
    }

    return new_block

async def create_new_block_header(transactions):
   
    timestamp = int(time.time() * 1000)
    version = "1.0.0"
    print("before creating new block")
    previous_block_header = await get_previous_block_header()
   
    # transactions_dict = [tx.to_dict() for tx in transactions]
    transactions = [tx.to_dict() if isinstance(tx, Transaction) else tx for tx in transactions]
    print("transactionsSENTMerkleTree", transactions)
    print("type of", type(transactions))
    merkle_tree = MerkleTree(transactions)
    print("before creating new block2")
    merkle_root = merkle_tree.get_merkle_root()
    difficulty = 0x1
    print("difficulty", difficulty)
    return BlockHeader(version, previous_block_header, merkle_root, timestamp, difficulty)

async def get_previous_block_header():
    
    # Get the total count of blocks in your blockchain
    total_blocks = await get_block_height()
    print("totalBlocks", total_blocks)
    previous_block_header = None

    if total_blocks > 0:
        # if blocks exist, get the last block's hash
        previous_block_header = (await get_block_from_leveldb(total_blocks))["block_header"]["hash"]
        print("totalblocks greater so this was called")
    elif total_blocks <= 0:
        # if no blocks exist yet (other than genesis), get the genesis block's hash
        previous_block_header = (await get_block_from_leveldb(0))["block_header"]["hash"]
        print("totalblocks less so this was called")
    else:
        # handle error case if total_blocks is less than 0
        raise ValueError("Invalid block count")

    return previous_block_header

async def update_difficulty():
    
    print("update_difficulty")
    target_block_time = 20000 # Target time per block in milliseconds
    TARGET_BLOCK_INTERVAL = 2 # Number of blocks for difficulty adjustment

    # Add a default difficulty value for the first block.
    default_difficulty = difficulty

    block_height = await get_block_height()

    print("blockHeight", block_height)

    # If there are no blocks in the blockchain, return the default difficulty.
    if block_height == 0:
        return default_difficulty

    if block_height < TARGET_BLOCK_INTERVAL or block_height % TARGET_BLOCK_INTERVAL != 0:
        print("blockHeight less than target block interval or block height % target block interval != 0")
        last_block = await get_block_from_leveldb(block_height - 1)

        return last_block["block_header"]["difficulty"]

    old_block = await get_block_from_leveldb(block_height - TARGET_BLOCK_INTERVAL)
    last_block = await get_block_from_leveldb(block_height - 1)

    time_difference = last_block["block_header"]["time"] - old_block["block_header"]["time"]
    print("timeDifference", time_difference)

    # Calculate the new difficulty
    new_difficulty = last_block["block_header"]["difficulty"]
    ideal_time = target_block_time * TARGET_BLOCK_INTERVAL
    ratio = ideal_time / time_difference

    new_difficulty = round(new_difficulty * ratio)

    print("newDifficulty", new_difficulty)

    # Convert new_difficulty to hexadecimal
    new_difficulty_hex = "0x" + hex(new_difficulty)[2:]

    print("newDifficulty in hexadecimal", new_difficulty_hex)

    return new_difficulty_hex


async def is_valid_new_block(new_block, previous_block):

    if not previous_block:
        # This is the first block. Perform specific genesis block checks.
        # For simplicity, we'll only check the index here.
        if new_block["index"] != 0:
            print("Error: The first block's index must be 0")
            return False
    else:
        # This is not the first block. Perform regular checks.
        if previous_block["index"] + 1 != new_block["index"]:
            print("Error: Invalid index")
            return False
        elif previous_block["block_header"]["hash"] != new_block["block_header"]["previousBlockHeader"]:
            print("Error: Invalid previous block header")
            return False
        else:
            # Construct a temporary block header with the hash inside for consistency in hashing
            temp_block = copy.deepcopy(new_block)
            temp_block["block_header"].pop("hash", None)

            
            block_string = json.dumps(temp_block, sort_keys=True)
            
            hash = calculate_hash_for_blockX(block_string)  # Ensure you have this function defined
           
            
            if hash != new_block["block_header"]["hash"]:
                print(f"Error: Invalid hash: {hash} {new_block['block_header']['hash']}")
                return False
    return True

async def store_block(new_block):
    # print("i'm in store block")
    # print("--------------------------------")
    # print(new_block)
    # print("--------------------------------")
    try:
        # Convert the Block object to a dictionary
        new_block_dict = new_block

        db.Put(("block_" + str(new_block_dict["index"])).encode("utf-8"), json.dumps(new_block_dict).encode("utf-8"))
        if new_block_dict["index"] != 0:
            print("--- Inserting block index: " + str(new_block_dict["index"]))
        return new_block
    except Exception as e:
        print("Error storing block:", e)
        raise e


async def add_block_to_chain(new_block):
    
    existing_block = await get_block_from_leveldb(new_block["index"])
    if existing_block:
        print(f"Block with index {new_block['index']} already exists, skipping")
        return

    total_blocks = await get_block_height()
    print("Current Local Block No:", total_blocks)

    previous_block = None
    if total_blocks > 0:
        previous_block = await get_block_from_leveldb(total_blocks)
        print("previous block was picked")
    elif total_blocks == 0:
        previous_block = await get_block_from_leveldb(0)
        print("Genesis Block was picked as previous block")
    else:
        raise Exception("Invalid block count")

    if not previous_block:
        print("Error: No previous block could be retrieved")
        return
    
   
    if await is_valid_new_block(new_block, previous_block):
       
        try:
            async with lock:
                try:
                    async def handle_single_transaction(transaction):
                        
                        if await validate_transaction(transaction):
                           
                            await store_transaction(transaction)
                            
                            remove_transactions([transaction])
                            
                            return transaction["fee"]
                        return 0

                    total_fee = 0
                    if isinstance(new_block["transactions"], list):
                        for transaction in new_block["transactions"]:
                            print("Handling multiple transactions")
                            total_fee += await handle_single_transaction(transaction)
                    else:
                        print("Handling single transaction")
                        total_fee = await handle_single_transaction(new_block["transactions"])

                    await reward_miner(new_block)
                    await store_block(new_block)
                    return new_block
                except Exception as e:
                    print("Error processing transaction:", e)
        except Exception as e:
            print("Error acquiring lock:", e)
    else:
        print("Error: Invalid block")

async def validate_transaction(transactions):
   
    if not isinstance(transactions, list):
        transactions = [transactions]

    valid = True
    loop = asyncio.get_event_loop()

    for transaction in transactions:

        # Check for coinbase Transaction
        
        if transaction["sender"] == "coinbase":
            print("coinbase transaction detected")
            continue # skip 

        # Load verifying key
        key_bytes = binascii.unhexlify(transaction["sender"])
        key = await loop.run_in_executor(None, VerifyingKey.from_string, key_bytes, SECP256k1)
        
        # Verify signature
        hash_to_verify = calculate_hash_for_transaction(transaction).encode("utf-8")
        try:
            valid_signature = key.verify(bytes.fromhex(transaction["signature"]), hash_to_verify)
        except BadSignatureError:
            print(f"Invalid transaction from {transaction['sender']} due to invalid signatureA")
            valid = False
            break
        
        print("valid_signature", valid_signature)
        if not valid_signature:
            print(f"Invalid transaction from {transaction['sender']} due to invalid signatureX")
            return False
        
        
        # Check balance and transfer
        try:
            sender_balance = await get_balance(transaction['sender'])
            
            sender_balance = sender_balance or 0
            if transaction['amount'] + TRANSACTION_FEE > sender_balance:
                print(f"Invalid transaction from {transaction['sender']} due to insufficient funds")
                valid = False
                break
            else:
                await update_balance(transaction['sender'], sender_balance - transaction['amount'] - TRANSACTION_FEE)
                receiver_balance = await get_balance(transaction['receiver'])
                receiver_balance = receiver_balance or 0
                await update_balance(transaction['receiver'], receiver_balance + transaction['amount'])
        except Exception as e:
            print("Error fetching balance:", e)
            valid = False
            break

    print("exit from validate transaction")
    return valid


def calculate_hash_for_transaction(transaction):
    
    transaction_string = transaction["sender"] + transaction["receiver"] + str(transaction["amount"]) + str(transaction["fee"]) + str(transaction["time"])
    hash_value = hashlib.sha256(transaction_string.encode("utf-8")).hexdigest()
    # print(f"The calculated hash is: {hash_value}")
    return hash_value


async def validate_transfer(transaction):
    if transaction["sender"] == "coinbase":
        print("coinbase transaction detected")
        await update_balance(transaction["receiver"], transaction["amount"])
        return True
    

   
    loop = asyncio.get_event_loop()
    key_bytes = binascii.unhexlify(transaction["sender"])
   
    key = await loop.run_in_executor(None, VerifyingKey.from_string, key_bytes, SECP256k1)
   
    hash_to_verify = calculate_hash_for_transaction(transaction).encode("utf-8")
    
    try:
        valid_signature = key.verify(bytes.fromhex(transaction["signature"]), hash_to_verify)
        
    except BadSignatureError:
        print(f"Invalid transaction from {transaction['sender']} due to invalid signatureP")
        return False
    
    

    if not valid_signature:
        print(f"Invalid transaction from {transaction['sender']} due to invalid signatureU")
        return False

    try:
        sender_balance = await get_balance(transaction["sender"])
        sender_balance = sender_balance or 0
        if transaction["amount"] + TRANSACTION_FEE > sender_balance:
            print(f"Invalid transaction from {transaction['sender']} due to insufficient funds")
            return False
        else:
            print("exit from validate transfer")
            return True
        
    except Exception as e:
        print("Error fetching balance:", e)
        return False


def block_to_string(block):
    block_str = {}
    for key, value in block.items():
        if isinstance(value, list):
            block_str[key] = [str(item) for item in value]
        elif hasattr(value, 'to_dict'):
            block_str[key] = value.to_dict()
        elif hasattr(value, '__str__'):
            block_str[key] = str(value)
        else:
            block_str[key] = value
    return block_str


async def create_and_add_transaction(block, transactions, miner_address):
    print("create transaction")
    try:
        async with lock:
            total_fee = 0
            async def handle_single_transaction(transaction):
                nonlocal total_fee
                transaction_dict = transaction.to_dict()
                if await validate_transfer(transaction_dict):
                    transaction_hash = calculate_hash_for_transaction(transaction_dict)
                    transaction_dict["id"] = transaction_hash
                    transaction_copy = copy.deepcopy(transaction_dict)
                    if not any((t["id"] if isinstance(t, dict) else t.id) == transaction_hash for t in block["transactions"]):
                        # Remove the transaction object if it exists in the block
                        block["transactions"] = [t for t in block["transactions"] if not isinstance(t, Transaction) or t.id != transaction.id]
                        block["tx"] = [t for t in block["tx"] if not isinstance(t, Transaction) or t.id != transaction.id]
                        block["transactions"].append(transaction_copy)
                        block["tx"].append(transaction_copy)
                        total_fee += transaction_copy["fee"]
                        print("exiting transaction")
                else:
                    print("Transaction validation failed.")
                    return


            if isinstance(transactions, list):
               
                for transaction in transactions:
                    print("Handling multiple transactions")
                    await handle_single_transaction(transaction)
            else:
                print("Handling single transaction")
               
                await handle_single_transaction(transactions)
            
            
            total_supply = await get_total_supply()
                
            total_supply_value = sum((t["amount"] for t in block["transactions"]))
            print("Sum of Transaction Amounts:", total_supply_value)
            final_value = total_supply + total_supply_value + total_fee
            print("Final Value:", final_value)


            print("total_supply", total_supply)
            if total_supply + sum((t["amount"] if isinstance(t, dict) else t['amount']) for t in block["transactions"]) + total_fee > MAX_SUPPLY:
                print("Error: These transactions would exceed the maximum supply of tokens")
                return

            miner_reward_transaction = {
                "sender": "coinbase",
                "receiver": miner_address,
                "amount": MINING_REWARD,
                "fee": total_fee,
                "signature": None,
                "time": int(time.time())
            }
            
            
            print("Minered transaction")
            miner_reward_transaction["id"] = calculate_hash_for_transaction(miner_reward_transaction)
            block["transactions"].insert(0, miner_reward_transaction)
           
            
            if isinstance(block, dict) and 'block_header' in block:
                if isinstance(block['block_header'], dict) or isinstance(block['block_header'], BlockHeader):
                    print("Came in isinstance 1st part")
                    print("BadAss", block["transactions"])
                    print("BadAss type", type(block["transactions"]))
                    # merkle_root_value = MerkleTree(block["transactions"]).get_merkle_root()
                    ids = [(t["id"] if isinstance(t, dict) else t['id']) for t in block["transactions"]]
                    if isinstance(ids, str):  # Check if it's just a single ID string
                        ids = [ids]
                    merkle_root_value = MerkleTree(ids).get_merkle_root()

                    print("merkle_root_value", merkle_root_value)
                    if isinstance(block['block_header'], dict):
                        print("Came in isinstance")
                        block["block_header"]["merkleRoot"] = merkle_root_value
                    else:  # instance of BlockHeader
                        print("Came in isinstance else part")
                        block['block_header'].merkleRoot = merkle_root_value
                        print("merkle_root_value2", block['block_header'].merkleRoot)
            elif hasattr(block, 'block_header'):
                print("Came in hasattr")
                block.block_header.merkleRoot = MerkleTree([(t.id if hasattr(t, 'id') else t["id"]) for t in block.transactions]).get_merkle_root()
            else:
                print("Error: Unrecognized block type")
                return

            return mine_hash(block)
    except Exception as e:
        print("Error processing transactionX:", e)



# kjqhdkqahkdaqhkhqkjdhqkjdhaqkhdkjaqhdkj

async def get_wallet_balance(user):
    try:
        balance = db.Get(("wallet-" + user).encode("utf-8"))
        # Convert bytearray to string, remove parentheses and comma, then convert to int
        balance = int(balance.decode("utf-8").strip("(,)"))
        return balance
    except KeyError:
        return 0
    except Exception as e:
        raise e



async def get_latest_block():
    block_height = await get_block_height()
    return await get_block_from_leveldb(block_height)

def get_db_block(index, res):
    try:
        value = db.Get(index)
        res.send(value)
    except Exception as e:
        res.send(json.dumps(e))

def get_block(index):
    if len(blockchain) - 1 >= index:
        return blockchain[index]
    else:
        return None

async def get_balance(user):
    try:
        balance = db.Get(("wallet-" + user).encode("utf-8"))
        # Convert bytearray to string, remove parentheses and comma, then convert to int
        balance = int(balance.decode("utf-8").strip("(,)"))
        return balance
    except KeyError:
        return 0
    except Exception as e:
        raise e



async def update_balance(user, amount):
    try:
        # Prepend 'wallet-' to the user key
        db.Put(("wallet-" + user).encode("utf-8"), str(amount).encode("utf-8"))
        return
    except Exception as e:
        print(f"Failed to update balance for {user}: ", e)
        raise e

async def get_block_from_leveldb(index):
    try:
        print("Inside get_block_from_leveldb")
        value = db.Get(("block_" + str(index)).encode("utf-8"))
        return json.loads(value.decode("utf-8"))
    except KeyError:
        print(f"Block with index {index} not found in the database.")
        return None
    except Exception as e:
        print(f"Block {index} get failed: {e}")
        raise e




async def store_transaction(transaction):
    print("=== Entering store_transaction ===")
    required_fields = ["sender", "receiver", "amount", "fee", "signature", "time", "id"]
    for field in required_fields:
        if field not in transaction:
            print(f"Error: '{field}' not found in the provided transaction.")
            return

    transaction_instance = {
        "sender": transaction["sender"],
        "receiver": transaction["receiver"],
        "amount": transaction["amount"],
        "fee": transaction["fee"],
        "signature": transaction["signature"],
        "time": transaction["time"],
        "id": transaction["id"]
    }
    try:
        # Verify the hashing function
        transaction_hash = calculate_hash_for_transaction(transaction_instance)
        print(f"Calculated transaction hash: {transaction_hash}")

        # Generate key with prefix and store the transaction
        db.Put(("transaction_" + str(transaction_hash)).encode("utf-8"), json.dumps(transaction_instance).encode("utf-8"))

        print(f"--- Stored transaction with hash: {transaction_hash} ---")
    except Exception as e:
        print("Error storing transaction:", e)
        raise e

    print("=== Exiting store_transaction ===")



async def get_transaction(transaction_hash):
    # Initialize the database connection
    # db = leveldb.LevelDB('./db/hello')

    # Add prefix to the transaction_hash before querying
    key_with_prefix = ("transaction_" + transaction_hash).encode("utf-8")

    try:
       
        value = db.Get(key_with_prefix)
        
        print("value", value)
        
        # Convert bytearray to string and load as JSON
        transaction_data = json.loads(value.decode("utf-8"))
        
        return transaction_data
    except KeyError:  # Adjust this if your database raises a different exception for missing entries.
        print(f"Transaction not found with hash: {transaction_hash}")
        return None
    except Exception as e:
        print(f"Error retrieving transaction: {e}")
        raise e



def print_all_transfers():
    print("=== Entered print_all ===")

    try:
        # Iterate through the database entries
        for key, value in db.RangeIter():
            decoded_key = key.decode("utf-8")
            print(f"Checking key: {decoded_key}")  # This line will print every key
            
            if decoded_key.startswith("transfers_"):
                print(f"Found transaction key: {decoded_key}, Value: {value.decode('utf-8')}")
    except Exception as e:
        print(f"Error accessing the database: {e}")
        raise e

    print("=== Exiting print_all ===")



async def get_block_height():
    def process_and_count_block(key, value):
        try:
            decoded_key = key.decode("utf-8")
            decoded_value = value.decode('utf-8')
            # print(f"Key: {decoded_key}")  
            if decoded_key.startswith("block_"):
                # print(f"Value: {decoded_value}")
                return True
        except Exception as e:
            print(f"Decoding error for key: {key}, value: {value}. Error: {e}")
        return False
    height = sum(1 for key, value in db.RangeIter() if process_and_count_block(key, value))
    
    print("heightX", height)
    return height - 1 



async def get_total_supply():
    total_supply = 0
    try:
        for key, value in db.RangeIter():
            try:
                if key.decode("utf-8").startswith("wallet-"):
                    decoded_value = eval(value.decode("utf-8"))
                    
                    if isinstance(decoded_value, tuple):
                        balance = decoded_value[0]
                    elif isinstance(decoded_value, int):
                        balance = decoded_value
                    else:
                        raise TypeError(f"Unexpected value type: {type(decoded_value)}")

                    total_supply += balance

            except (UnicodeDecodeError, SyntaxError, IndexError, TypeError) as inner_error:
                print(f"Error while processing key-value pair ({key}, {value}): {inner_error}")

    except Exception as outer_error:
        print(f"Error during db iteration: {outer_error}")

    return total_supply



