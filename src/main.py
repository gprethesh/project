
import hashlib
import json

class BlockHeader:
    def __init__(self, version, previousBlockHeader, merkleRoot, time, difficulty):
        self.version = version
        self.previousBlockHeader = previousBlockHeader
        self.merkleRoot = merkleRoot
        self.time = time
        self.difficulty = difficulty
        
    def to_dict(self):
        return {
            'version': self.version,
            'previousBlockHeader': self.previousBlockHeader,
            'merkleRoot': self.merkleRoot,
            'time': self.time,
            'difficulty': self.difficulty
        }
    def __str__(self):
        return ', '.join(f'{attr}={getattr(self, attr)}' for attr in vars(self))


class Block:
    def __init__(self, blockHeader, index, transactions, tx):
        self.blockHeader = blockHeader
        self.index = index
        self.transactions = transactions
        self.tx = tx
        self.nonce = 0
        self.blockHeader.merkleRoot = self.calculateMerkleRoot(transactions)
        
    def __str__(self):
        return json.dumps(self.to_dict(), indent=4)
        
    def to_dict(self):
        return {
            'block_header': self.blockHeader.__dict__,
            'index': self.index,
            'transactions': [tx.__dict__ for tx in self.transactions],
            'tx': [tx.__dict__ for tx in self.tx],
            'nonce': self.nonce,
        }
        
    def calculateMerkleRoot(self, transactions):
        transactionHashes = [transaction.calculate_hash() for transaction in transactions]
        if len(transactionHashes) == 1:
            return transactionHashes[0]
        while len(transactionHashes) > 1:
            if len(transactionHashes) % 2 != 0:
                transactionHashes.append(transactionHashes[-1])
            newHashes = []
            for i in range(0, len(transactionHashes), 2):
                newHashes.append(hashlib.sha256((transactionHashes[i] + transactionHashes[i + 1]).encode()).hexdigest())
            transactionHashes = newHashes
        return transactionHashes[0]

class Transaction:
    def __init__(self, sender, receiver, amount, fee, signature, time, id):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.signature = signature
        self.fee = fee
        self.time = time
        self.id = id
        
    def to_dict(self):
        # Check if signature is bytes
        if isinstance(self.signature, bytes):
            signature = self.signature.hex()  # convert bytes to hexadecimal
        else:
            signature = self.signature  # leave it as is if it's already a string

        transaction_dict = {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'fee': self.fee,
            'signature': signature,
            'time': self.time,
            'id': self.id
        }
        # print(transaction_dict)  # This will print the dictionary
        return transaction_dict


    def calculate_hash(self):
        return hashlib.sha256((self.sender + self.receiver + str(self.amount) + str(self.fee) + str(self.time)).encode()).hexdigest()
    # def __str__(self):
    #     return ', '.join(f'{attr}={getattr(self, attr)}' for attr in vars(self))