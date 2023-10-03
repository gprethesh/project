import asyncio
import json

# Assuming create_db and get_transaction are defined somewhere else.
from chain import create_db, get_transaction, print_all_transfers


async def test_get_transaction():
    await create_db("hello")  # Ensure db is initialized.
    
    # print_all_transfers()
    #Fetching transactions from the database using get_transaction.
    tx1 = await get_transaction("32ea19a4029c5434cd0f6f594887427e6c76e55ce68dd14361e2d2cd2bc71fa0")
    print(f"Transaction 1: {tx1}")
    print("##"*150)
    tx2 = await get_transaction("c77b5fbee350008754250fabab3e2dd499ce23f4288b14ee39af0f3c4a87a0d8")
    print(f"Transaction 1: {tx2}")
# Run the async function to test.
asyncio.run(test_get_transaction())
