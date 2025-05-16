import json
import os

LEDGER_DIR = "data/ledger/"

for filename in os.listdir(LEDGER_DIR):
    path = os.path.join(LEDGER_DIR, filename)
    print(f"\n📘 Ledger for account: {filename}")
    with open(path, "r") as f:
        for line in f:
            print(json.dumps(json.loads(line), indent=2))
