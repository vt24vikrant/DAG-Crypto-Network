import asyncio

import websockets

from cli import cli_loop
from config import DEFAULT_PORT
from crypto_utils import generate_rsa_keys
from network import handle_connection


async def start_server(rsa_keys):
    async def handler(websocket, path):
        await handle_connection(websocket, path, rsa_keys)

    print(f"🌐 P2P Server listening on ws://localhost:{DEFAULT_PORT}")
    return await websockets.serve(handler, "localhost", DEFAULT_PORT)

async def main():
    rsa_keys = generate_rsa_keys()
    await start_server(rsa_keys)
    await cli_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Node shut down manually.")