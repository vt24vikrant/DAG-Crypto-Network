import asyncio
import json
import uuid

from crypto_utils import load_or_generate_signing_key, sign_data
from ledger import get_balance
from node import (connected_nodes, process_transaction, receive_vote,
                  register_node, vote_pool)


async def cli_loop():
    print("📡 Interface")
    print("-----------------------")
    print("1. Register Node")
    print("2. Submit Transaction")
    print("3. Vote on Transaction")
    print("4. Show Vote Pool")
    print("5. Show Reputations")
    print("6. Exit")
    print("7. Connect to peer")  # Added option 7

    signing_key = load_or_generate_signing_key()
    address = signing_key.verify_key.encode().hex()[:16]  # short fake address for demo

    while True:
        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            port = input("Enter port (e.g., 9000): ")
            weight = float(input("Enter voting weight: "))
            register_node(f"127.0.0.1:{port}", is_full=True, weight=weight)
            print("✅ Node registered.")

        elif choice == "2":
            tx_type = input("Transaction type (send/receive/open): ")
            previous = input("Previous block ID (or 000..0 for open): ")
            balance = input("New balance after tx: ")

            tx = {
                "id": str(uuid.uuid4().hex),
                "type": tx_type,
                "address": address,
                "previous": previous,
                "balance": balance,
            }
            tx["signature"] = sign_data(tx, signing_key)
            result = await process_transaction(tx)
            print(json.dumps(result, indent=2))

        elif choice == "3":
            tx_id = input("Transaction ID to vote on: ")
            node = input("Your node address (e.g., 127.0.0.1:9000): ")
            vote = input("Vote yes? (y/n): ").lower() == "y"
            result = await receive_vote(tx_id, node, vote)
            print(json.dumps(result, indent=2))

        elif choice == "4":
            print("\n📜 Vote Pool:")
            for tx_id, details in vote_pool.items():
                print(f"- {tx_id}: confirmed={details['confirmed']}, votes={len(details['votes'])}")

        elif choice == "5":
            print("\n📈 Reputations:")
            for node, info in connected_nodes.items():
                print(f"- {node}: reputation={info['reputation']}, weight={info['weight']}")

        elif choice == "6":
            print("Exiting CLI.")
            break

        elif choice == "7":  # Added block for connecting to a peer
            from network import connect_to_peer
            port = input("Peer port (e.g., 9001): ")
            url = f"ws://localhost:{port}"
            from crypto_utils import generate_rsa_keys
            rsa_keys = generate_rsa_keys()
            await connect_to_peer(url, rsa_keys)
            print(f"✅ Connected to peer at {url}")

        else:
            print("❌ Invalid option. Try again.")