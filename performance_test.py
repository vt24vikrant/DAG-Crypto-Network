import asyncio
import time
import uuid
from statistics import mean

from crypto_utils import (load_or_generate_signing_key, sign_data,
                          verify_signature)
from ledger import get_head_block
from node import process_transaction, receive_vote, register_node, vote_pool

# Setup: n nodes, same as simulate_network
nodes = {
    "A": {"port": 9000, "weight": 5},
    "B": {"port": 9001, "weight": 5},
    "C": {"port": 9002, "weight": 50},
    "D": {"port": 9003, "weight": 50},
    "E": {"port": 9004, "weight": 20},
    "F": {"port": 9005, "weight": 2},
    "G": {"port": 9006, "weight": 10},
    "H": {"port": 9007, "weight": 25},
    # "I": {"port": 9008, "weight": 8},
    # "J": {"port": 9009, "weight": 15},
    "K": {"port": 9010, "weight": 50},
    # "L": {"port": 9011, "weight": 50},
    # "M": {"port": 9012, "weight": 20},
    # "N": {"port": 9013, "weight": 2},
    # "O": {"port": 9014, "weight": 10},
}

NUM_TRANSACTIONS = 10
node_keys = {}
latencies = []

async def setup_nodes():
    print("🔧 Registering nodes...")
    for name, info in nodes.items():
        addr = f"127.0.0.1:{info['port']}"
        signing_key = load_or_generate_signing_key()
        pub_key = signing_key.verify_key.encode().hex()
        register_node(addr, is_full=True, weight=info["weight"], public_key_hex=pub_key)
        node_keys[name] = {
            "address": addr,
            "key": signing_key,
            "public_key_hex": pub_key,
        }

async def validate_transaction_for_voting(tx_id):
    try:
        tx = vote_pool[tx_id]["tx"]
        if not verify_signature(tx, tx["signature"], tx["address"]):
            return False
        try:
            head = await get_head_block(tx["address"])
            if tx["previous"] != head["id"]:
                return False
            if float(tx["balance"]) > float(head["balance"]):
                return False
        except:
            if tx["previous"] != "0" * 20:
                return False
        if "receiver" not in tx or len(tx["receiver"]) < 10:
            return False
        return True
    except:
        return False

async def simulate_transaction(i):
    sender = "B"
    receiver = "A"
    sender_key = node_keys[sender]["key"]
    sender_pub = node_keys[sender]["public_key_hex"]
    receiver_pub = node_keys[receiver]["public_key_hex"]

    tx_id = uuid.uuid4().hex

    try:
        # Get latest block to set 'previous' and calculate balance
        head = await get_head_block(sender_pub)
        previous = head["id"]
        new_balance = str(float(head["balance"]))
    except:
        # First transaction (genesis)
        previous = "0" * 20
        new_balance = "20.0"  # Starting balance

    tx = {
        "id": tx_id,
        "type": "send",
        "address": sender_pub,
        "receiver": receiver_pub,
        "previous": previous,
        "balance": new_balance,
        "timestamp_submitted": time.time(),
    }

    tx["signature"] = sign_data(tx, sender_key).hex()

    result = await process_transaction(tx)
    if result["status"] != "pending":
        print(f"❌ Tx {i+1} rejected: {result['reason']}")
        return False

    for name in ["C", "D", "E"]:
        voter_addr = node_keys[name]["address"]
        vote_yes = await validate_transaction_for_voting(tx_id)
        await receive_vote(tx_id, voter_addr, vote_yes)

    for _ in range(20):  # Increased timeout to 2 seconds
        await asyncio.sleep(0.05)
        if vote_pool.get(tx_id, {}).get("confirmed"):
            latency = time.time() - tx["timestamp_submitted"]
            latencies.append(latency)
            return True

    print(f"⚠️ Tx {i+1} timed out.")
    return False


async def main():
    await setup_nodes()
    print(f"\n🚀 Running parallel test for {NUM_TRANSACTIONS} transactions...\n")

    start = time.time()
    success_count = 0

    # Step 1: Send genesis transaction sequentially
    print("🔹 Sending genesis transaction...")
    ok = await simulate_transaction(0)
    if ok:
        success_count += 1
    else:
        print("❌ Genesis transaction failed. Aborting test.")
        return

    # Step 2: Launch remaining transactions (1 to N-1) in parallel
    tasks = [simulate_transaction(i) for i in range(1, NUM_TRANSACTIONS)]
    results = await asyncio.gather(*tasks)
    success_count += sum(results)

    end = time.time()
    duration = end - start
    tps = success_count / duration if duration > 0 else 0
    avg_latency = mean(latencies) if latencies else 0

    print("\n📊 Parallel Performance Report")
    print(f" Successful: {success_count}/{NUM_TRANSACTIONS}")
    print(f" TPS: {tps:.2f}")
    print(f" Avg Latency: {avg_latency:.4f} seconds")
    print(f" Total Duration: {duration:.2f} seconds")


if __name__ == "__main__":
    asyncio.run(main())