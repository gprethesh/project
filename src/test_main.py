from main import BlockHeader, Block, Transaction

def test_blockchain():
    # create transactions
    tx1 = Transaction("Alice", "Bob", 10, 1, "signature1", "2022-01-01 00:00:00", 1)
    tx2 = Transaction("Bob", "Charlie", 5, 1, "signature2", "2022-01-01 00:01:00", 2)
    tx3 = Transaction("Charlie", "Alice", 3, 1, "signature3", "2022-01-01 00:02:00", 3)

    # create block header
    blockHeader = BlockHeader(1, "previousBlockHeaderHash", "", "2022-01-01 00:00:00", 1)

    # create block
    block = Block(blockHeader, 1, [tx1, tx2, tx3], "")

    # print block information
    print("Block index:", block.index)
    print("Block nonce:", block.nonce)
    print("Block merkle root:", block.blockHeader.merkleRoot)
    print("Block transactions:")
    for tx in block.transactions:
        print("  Transaction ID:", tx.id)
        print("  Transaction sender:", tx.sender)
        print("  Transaction receiver:", tx.receiver)
        print("  Transaction amount:", tx.amount)
        print("  Transaction fee:", tx.fee)
        print("  Transaction signature:", tx.signature)
        print("  Transaction time:", tx.time)
        print("  Transaction hash:", tx.calculateHash())
        print()

test_blockchain()