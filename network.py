import asyncio
import json
from collections import defaultdict

import websockets

from config import BOOTSTRAP_PORT
from crypto_utils import aes_decrypt, aes_encrypt, rsa_decrypt, rsa_encrypt
from node import process_transaction, receive_vote

# In-memory peers list
peers = {}  # {node_url: {"ws": websocket, "session_key": bytes}}

# Bootstrap public key exchange and AES key setup
async def perform_handshake(ws, private_rsa_key, public_rsa_key):
    # Step 1: Send public RSA key
    await ws.send(public_rsa_key.export_key().decode())

    # Step 2: Receive AES session key encrypted with our public RSA key
    encrypted_data = await ws.recv()
    encrypted_key = bytes.fromhex(encrypted_data)
    session_key = rsa_decrypt(private_rsa_key, encrypted_key)

    return session_key

async def connect_to_peer(url, rsa_keys):
    try:
        ws = await websockets.connect(url)
        session_key = await perform_handshake(ws, rsa_keys[0], rsa_keys[1])
        peers[url] = {"ws": ws, "session_key": session_key}
        print(f"Connected to peer {url}")
    except Exception as e:
        print(f"Failed to connect to {url}: {e}")

async def broadcast_transaction(tx):
    for url, conn in peers.items():
        packet = {"type": "transaction", "tx": tx}
        await send_secure_message(conn["ws"], conn["session_key"], packet)

async def broadcast_vote(tx_id, node_address, vote):
    for url, conn in peers.items():
        packet = {"type": "vote", "vote": vote, "tx_id": tx_id, "node": node_address}
        await send_secure_message(conn["ws"], conn["session_key"], packet)

async def send_secure_message(ws, session_key, message):
    data = json.dumps(message)
    encrypted = aes_encrypt(session_key, data)
    await ws.send(json.dumps(encrypted))

# Incoming request handler (per connection)
async def handle_connection(websocket, path, rsa_keys):
    # Receive their public RSA key
    client_pubkey_pem = await websocket.recv()
    client_pubkey = rsa_keys[0].import_key(client_pubkey_pem)

    # Send AES session key encrypted with their pubkey
    session_key = rsa_keys[0].get_random_bytes(16)
    encrypted_key = rsa_encrypt(client_pubkey, session_key)
    await websocket.send(encrypted_key.hex())

    # Message loop
    try:
        while True:
            data = await websocket.recv()
            try:
                encrypted_data = json.loads(data)
                decrypted = aes_decrypt(session_key, encrypted_data)
                message = json.loads(decrypted)
            except:
                print("Failed to decrypt or parse message")
                continue

            if message["type"] == "transaction":
                await process_transaction(message["tx"])

            elif message["type"] == "vote":
                await receive_vote(message["tx_id"], message["node"], message["vote"])

    except websockets.ConnectionClosed:
        print("Peer disconnected.")
