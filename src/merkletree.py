import hashlib
import json

def calculate_hash(data):
    # Check if data is a dictionary. If so, convert it to a JSON string
    if isinstance(data, dict):
        data = json.dumps(data)
    # If it's not a string by now, convert it using str()
    if not isinstance(data, str):
        data = str(data)
    return hashlib.sha256(data.encode()).hexdigest()

class MerkleTree:
    def __init__(self, transactions):
        print("YYY", transactions)
        self.tree = self.build_tree(transactions)

    def build_tree(self, transactions):
        tree = []
        print("XXX", transactions)
        print("STEP1")
        for i in range(len(transactions)):
            print("STEP2")
            # Check if the transaction is a dictionary
            if isinstance(transactions[i], dict):
                print(type(transactions[i].get('signature', 'None')))
                print("STEP3")
            # Check if the transaction has a 'signature' attribute
            elif hasattr(transactions[i], 'signature'):
                print(type(transactions[i].signature))
            # If it's neither a dictionary nor has a 'signature' attribute, it's a plain string
            elif isinstance(transactions[i], str):
                print("Handling string transaction")
            else:
                print(f"Unsupported type: {type(transactions[i])}")
            print("STEP4")
            # Calculate the hash for the transaction
            tree.append(calculate_hash(transactions[i].to_dict() if hasattr(transactions[i], 'to_dict') else transactions[i]))

        tree_layer = tree
        while len(tree_layer) > 1:
            tree_layer = self.calculate_next_layer(tree_layer)
            print("Next layer:", tree_layer)
            tree = tree_layer + tree
        return tree

    def calculate_next_layer(self, nodes):
        next_layer = []
        for i in range(0, len(nodes), 2):
            if i + 1 < len(nodes):
                next_layer.append(calculate_hash(nodes[i] + nodes[i + 1]))
            else:
                next_layer.append(calculate_hash(nodes[i]))
        return next_layer

    def get_merkle_root(self):
        return self.tree[0]
