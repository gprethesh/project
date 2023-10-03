transaction_pool = []

def add_to_transaction_pool(transaction):
    print("Added to Pool")
    transaction_pool.append(transaction)

def get_transaction_pool():
    return transaction_pool

def remove_transactions(transactions_to_remove):
    global transaction_pool
    transaction_pool = [tp_transaction for tp_transaction in transaction_pool 
                        if not any(rt_transaction['id'] == tp_transaction['id'] 
                                   for rt_transaction in transactions_to_remove)]

if __name__ == "__main__":
    # You can add some sample test cases here if needed.
    pass
