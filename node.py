import asyncio
import json

from config import (CONSENSUS_THRESHOLD, REPUTATION_INCREMENT, REPUTATION_INIT,
                    REPUTATION_PENALTY)
from crypto_utils import verify_signature
from ledger import append_block, get_head_block

# In-memory state
connected_nodes = {}  # { node_address: {"is_full": True, "reputation": 10, "weight": 100.0, "public_key": ...} }
vote_pool = {}        # { tx_id: {"votes": [], "threshold": 100.0, "confirmed": False, "tx": {..}} }

# Register a node into the system
def register_node(node_address, is_full=True, weight=0.0, public_key_hex=None):
    connected_nodes[node_address] = {
        "is_full": is_full,
        "weight": weight,
        "reputation": REPUTATION_INIT,
        "public_key": public_key_hex
    }

def update_reputation(node_address, correct=True):
    if node_address in connected_nodes:
        if correct:
            connected_nodes[node_address]["reputation"] += REPUTATION_INCREMENT
        else:
            connected_nodes[node_address]["reputation"] -= REPUTATION_PENALTY

def get_voting_weight(node_address):
    return connected_nodes.get(node_address, {}).get("weight", 0.0)

def is_full_node(node_address):
    return connected_nodes.get(node_address, {}).get("is_full", False)

# Process a new transaction and broadcast it
async def process_transaction(tx):
    from network import broadcast_transaction  # Avoid circular dependency

    tx_id = tx["id"]

    # Verify signature against provided public key
    valid = verify_signature(tx, tx["signature"], tx["address"])
    if not valid:
        return {"status": "rejected", "reason": "invalid signature"}

    # Validate ledger history
    try:
        head = await get_head_block(tx["address"])
        if tx["previous"] != head["id"]:
            return {"status": "rejected", "reason": "invalid previous"}
        if float(tx["balance"]) > float(head["balance"]):
            return {"status": "rejected", "reason": "overspend"}
    except:
        if tx["previous"] != "0" * 20:
            return {"status": "rejected", "reason": "invalid open"}

    # Create a vote pool
    total_weight = sum(n["weight"] for n in connected_nodes.values() if n["is_full"])
    threshold = CONSENSUS_THRESHOLD * total_weight
    vote_pool[tx_id] = {"votes": [], "threshold": threshold, "confirmed": False, "tx": tx}

    # Broadcast transaction to the network
    await broadcast_transaction(tx)

    return {"status": "pending", "tx_id": tx_id}

# Handle vote reception and check for consensus
async def receive_vote(tx_id, node_address, vote_yes):
    from network import broadcast_vote  # Avoid circular dependency

    if not is_full_node(node_address):
        return {"status": "rejected", "reason": "not eligible to vote"}

    vote_weight = get_voting_weight(node_address)
    vote_pool[tx_id]["votes"].append((node_address, vote_yes, vote_weight))

    # Tally votes
    yes_weight = sum(w for _, v, w in vote_pool[tx_id]["votes"] if v)
    if not vote_pool[tx_id]["confirmed"] and yes_weight >= vote_pool[tx_id]["threshold"]:
        tx = vote_pool[tx_id]["tx"]
        sender_address = tx["address"]
        receiver_address = tx.get("receiver")

        # 1. Add send block to sender ledger
        await append_block(sender_address, tx)

        # 2. Create and append receive block
        if receiver_address:
            receive_block = {
                "id": f"{tx['id']}_recv",
                "type": "receive",
                "source": tx["id"],
                "previous": "0" * 20,
                "balance": tx["balance"]
            }

            try:
                head = await get_head_block(receiver_address)
                receive_block["previous"] = head["id"]
                new_balance = float(head["balance"]) + float(tx["balance"])
                receive_block["balance"] = str(new_balance)
            except:
                receive_block["previous"] = "0" * 20
                receive_block["balance"] = tx["balance"]

            await append_block(receiver_address, receive_block)

        # Mark transaction as confirmed
        vote_pool[tx_id]["confirmed"] = True

        # Update reputations for correct voters
        for n, voted_yes, _ in vote_pool[tx_id]["votes"]:
            update_reputation(n, correct=(voted_yes is True))

        # Broadcast vote result
        await broadcast_vote(tx_id, node_address, vote_yes)
        return {"status": "confirmed", "tx": tx}

    # If not confirmed yet, just record the vote
    await broadcast_vote(tx_id, node_address, vote_yes)
    return {"status": "vote received", "yes_weight": yes_weight}