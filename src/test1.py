from main import BlockHeader, Block, Transaction
import hashlib

def calculate_hash_for_block(block):
    # Convert all block attributes to strings
    version = str(block['blockHeader']['version'])
    previous_block_header = str(block['blockHeader']['previousBlockHeader'])
    merkle_root = str(block['blockHeader']['merkleRoot'])
    timestamp = str(block['blockHeader']['time'])
    difficulty = str(block['blockHeader']['difficulty'])

    # Concatenate the block attributes
    block_string = version + previous_block_header + merkle_root + timestamp + difficulty

    # Convert the block string to bytes
    data = block_string.encode('utf-8')

    # Calculate the SHA-256 hash
    sha256_hash = hashlib.sha256(data)

    return sha256_hash.hexdigest()


async def create_genesis_block():
    timestamp = 1690365924213
    previous_block_header = "0000000000000000000000000000000000000000000000000000000000000000"
    version = "1.0.0"
    merkle_root = "bb77e380f6d0ae7a842dc47a11b4d6a46523b05295eb86d4a583e59b90c1cbb5"
    difficulty= "0x1"
    block_header = BlockHeader(version, previous_block_header, merkle_root, timestamp, difficulty)

    # Create a transaction
    sender = "genesis"
    receiver = "04227ea4320cfd7d50fd821b3cc66d7bcbd80a8806dc3e5ce90fba3c6594920c482d6360933fd149363d5d1177320e108d836165ae48ece6d9c54919565c2f0562"
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

    return block


if __name__ == '__main__':
    import asyncio

    async def main():
        block = await create_genesis_block()
        print("Genesis block:", block)

    asyncio.run(main())