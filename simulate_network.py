import asyncio
import time
import uuid

from crypto_utils import (load_or_generate_signing_key, sign_data,
                          verify_signature)
from ledger import get_head_block
from node import process_transaction, receive_vote, register_node, vote_pool

# Define simulated nodes
nodes = {
    "A": {"port": 9000, "weight": 5},
    "B": {"port": 9001, "weight": 5},
    "C": {"port": 9002, "weight": 50},
    "D": {"port": 9003, "weight": 50},
    "E": {"port": 9004, "weight": 50},
}

node_keys = {}

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
        print(f"✅ Node {name} registered at {addr} with pubkey {pub_key[:12]}...")

async def simulate_transaction():
    sender = "B"
    receiver = "A"
    tx_id = uuid.uuid4().hex

    sender_key = node_keys[sender]["key"]
    sender_pub = node_keys[sender]["public_key_hex"]
    receiver_pub = node_keys[receiver]["public_key_hex"]

    tx = {
        "id": tx_id,
        "type": "send",
        "address": sender_pub,
        "receiver": receiver_pub,
        "previous": "0" * 20,
        "balance": "90.0",
        "timestamp_submitted": time.time(),
    }
    tx["signature"] = sign_data(tx, sender_key).hex()

    print(f"\n📤 {sender} is sending 90.0 to {receiver}")
    print(f"Sender:   {sender_pub[:12]}...")
    print(f"Receiver: {receiver_pub[:12]}...")

    result = await process_transaction(tx)
    print(f"🧾 Transaction status: {result}")
    return tx_id if result["status"] == "pending" else None

async def validate_transaction_for_voting(tx_id):
    try:
        tx = vote_pool[tx_id]["tx"]

        if not verify_signature(tx, tx["signature"], tx["address"]):
            print(f"🚫 Invalid signature in tx {tx_id}")
            return False

        try:
            head = await get_head_block(tx["address"])
            if tx["previous"] != head["id"]:
                print(f"🚫 Invalid previous block in tx {tx_id}")
                return False
            if float(tx["balance"]) > float(head["balance"]):
                print(f"🚫 Overspend in tx {tx_id}")
                return False
        except:
            if tx["previous"] != "0" * 20:
                print(f"🚫 Invalid genesis in tx {tx_id}")
                return False

        if "receiver" not in tx or len(tx["receiver"]) < 10:
            print(f"🚫 Invalid receiver in tx {tx_id}")
            return False

        return True
    except Exception as e:
        print(f"🚫 Error during validation of tx {tx_id}: {e}")
        return False

async def simulate_voting(tx_id):
    print("\n🗳 Voting starts...")
    for name in ["C", "D", "E"]:
        voter_addr = node_keys[name]["address"]
        vote_yes = await validate_transaction_for_voting(tx_id)
        result = await receive_vote(tx_id, voter_addr, vote_yes)
        vote_str = "YES" if vote_yes else "NO"
        print(f"🗳 {name} voted {vote_str} on tx {tx_id} → {result['status']}")

async def display_result(tx_id):
    await asyncio.sleep(1)
    pool = vote_pool.get(tx_id)
    if pool:
        status = "✅ Confirmed" if pool["confirmed"] else "❌ Not confirmed"
        print(f"\n📦 Final result for tx {tx_id}: {status}")
    else:
        print("⚠️ Vote pool not found.")

async def main():
    await setup_nodes()
    tx_id = await simulate_transaction()
    if tx_id:
        await asyncio.sleep(1)
        await simulate_voting(tx_id)
        await display_result(tx_id)

if __name__ == "__main__":
    asyncio.run(main())
