import json
import os

import aiofiles

from config import LEDGER_DIR

os.makedirs(LEDGER_DIR, exist_ok=True)

async def get_account_file_path(address):
    return os.path.join(LEDGER_DIR, address)

async def get_head_block(address):
    path = await get_account_file_path(address)
    if not os.path.exists(path):
        raise FileNotFoundError("Account not found")
    async with aiofiles.open(path, 'r') as f:
        lines = await f.readlines()
        if not lines:
            raise ValueError("No blocks found")
        return json.loads(lines[-1])

async def append_block(address, block):
    path = await get_account_file_path(address)
    async with aiofiles.open(path, 'a') as f:
        await f.write(json.dumps(block) + '\n')

async def get_balance(address):
    try:
        block = await get_head_block(address)
        return float(block["balance"])
    except Exception:
        return 0.0

async def get_all_accounts():
    return [f for f in os.listdir(LEDGER_DIR) if os.path.isfile(os.path.join(LEDGER_DIR, f))]
